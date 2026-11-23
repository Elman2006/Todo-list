# ============================================================
# database.py  —  All SQLite operations live here
# ============================================================
# ROOT CAUSE FIXED:
#   The original file had TWO different connection strategies:
#     • init_db()        used a fresh context-manager connection
#     • get_connection() kept a persistent reusable connection
#   These two strategies can diverge (one commits, the other
#   doesn't see the change).  Now init_db() also calls
#   get_connection() so there is ONE connection for the whole
#   lifetime of the DatabaseManager object.
# ============================================================

import sqlite3
import logging
from typing import List, Optional, Tuple
# NEW: Optional is used for the deadline (a project may have no deadline).

# Standard Python logging — writes messages to the console so
# we can see what the database is doing without print().
logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages all reads and writes to the SQLite database.

    One instance should be created in main.py and shared with
    every frame via the AppController.  Do NOT create extra
    instances inside individual frames (was a bug in the
    original BottomFrame).
    """

    def __init__(self, db_path: str = "projects.db"):
        # Path to the SQLite file on disk
        # NOTE (round 6): "projects.db" is a RELATIVE path, so the file is created
        # in the folder you start the program from. Run `python main.py` from the
        # project folder and it sits right next to the source files. (The app
        # runs directly from source; there is no packaged / installed version.)
        self.db_path = db_path

        # The single persistent connection — None until first use
        self.connection = None

        # Create tables if they don't exist yet
        self.init_db()

    # ----------------------------------------------------------
    # Connection management
    # ----------------------------------------------------------

    def get_connection(self) -> sqlite3.Connection:
        """
        Return the persistent connection, creating it on first call.

        check_same_thread=False  →  required because tkinter's
        event loop runs on the main thread but we want one shared
        connection object.  SQLite itself is thread-safe in
        serialised mode (the default).

        timeout=10  →  wait up to 10 s if another operation has
        locked the file before raising an error.
        """
        if self.connection is None:
            self.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=10
            )
            # Enable foreign-key enforcement (OFF by default in SQLite)
            self.connection.execute("PRAGMA foreign_keys = ON")

        return self.connection

    def close_connection(self):
        """
        Cleanly close the connection.  Call this when the app exits.
        """
        if self.connection:
            self.connection.close()
            self.connection = None

    # ----------------------------------------------------------
    # Schema initialisation
    # ----------------------------------------------------------

    def init_db(self):
        """
        Create the projects and tasks tables if they do not exist.

        FIX: now uses get_connection() instead of a separate
        sqlite3.connect() call, so there is no risk of two
        connections seeing different states.
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # --- Projects table ---
            # Each project has a unique title so duplicates are
            # caught by the database, not just the Python code.
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    title      TEXT    NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # --- Tasks table ---
            # ON DELETE CASCADE means deleting a project also
            # automatically deletes all its tasks — no orphans.
            #
            # NEW: "notes" column added to support the editable
            # "task details/content" field requested for the
            # rename/edit feature. It is nullable so it has no
            # effect on any existing row.
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id  INTEGER NOT NULL,
                    description TEXT    NOT NULL,
                    notes       TEXT    DEFAULT NULL,
                    completed   BOOLEAN DEFAULT 0,
                    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id)
                        REFERENCES projects (id)
                        ON DELETE CASCADE
                )
            """)

            # --- Migration for existing databases -------------
            # If projects.db was created by an EARLIER version of
            # this app (before the "notes" column existed), the
            # CREATE TABLE IF NOT EXISTS above is a no-op and the
            # old table is kept as-is. This check adds the missing
            # column without touching any existing data, so nothing
            # the user already saved is lost or altered.
            cursor.execute("PRAGMA table_info(tasks)")
            existing_columns = [row[1] for row in cursor.fetchall()]
            if "notes" not in existing_columns:
                cursor.execute("ALTER TABLE tasks ADD COLUMN notes TEXT DEFAULT NULL")

            # ----------------------------------------------------------
            # NEW (drag-and-drop + deadlines): three more columns, all
            # added through the SAME migration pattern as "notes" above.
            # The CREATE TABLE statements above are intentionally left
            # untouched; a brand-new database simply gets the columns
            # added a few lines later, so fresh and existing databases
            # end up with an identical schema.
            #
            #   projects.position  -> manual sort order (lower = higher up)
            #   projects.deadline  -> ISO date text "YYYY-MM-DD" or NULL
            #   tasks.position     -> manual sort order inside one project
            #
            # NOTE: the column is called "position" (not "order")
            # because ORDER is a reserved word in SQL.
            # ----------------------------------------------------------
            cursor.execute("PRAGMA table_info(projects)")
            project_columns = [row[1] for row in cursor.fetchall()]

            if "deadline" not in project_columns:
                cursor.execute("ALTER TABLE projects ADD COLUMN deadline TEXT DEFAULT NULL")

            # NEW (bell / notifications): projects.muted = 1 means "do not
            # include this project in the launch reminders". It is a normal
            # SQLite BOOLEAN (stored as 0 or 1) and defaults to 0 = unmuted,
            # so every existing project keeps behaving exactly as before.
            if "muted" not in project_columns:
                cursor.execute("ALTER TABLE projects ADD COLUMN muted BOOLEAN DEFAULT 0")

            if "position" not in project_columns:
                cursor.execute("ALTER TABLE projects ADD COLUMN position INTEGER DEFAULT 0")
                # Backfill: give every EXISTING project a position that
                # reproduces the order the user sees today (newest first,
                # highest id first when two share the same timestamp).
                # Done in plain Python on purpose: SQL window functions
                # would need SQLite 3.25+, which older Pythons lack.
                cursor.execute("SELECT id FROM projects ORDER BY created_at DESC, id DESC")
                ordered_ids = [row[0] for row in cursor.fetchall()]
                cursor.executemany(
                    "UPDATE projects SET position = ? WHERE id = ?",
                    [(pos, pid) for pos, pid in enumerate(ordered_ids)]
                )

            if "position" not in existing_columns:
                cursor.execute("ALTER TABLE tasks ADD COLUMN position INTEGER DEFAULT 0")
                # Same backfill, but numbered separately inside each project
                # so every project's tasks keep their current newest-first order.
                cursor.execute("SELECT DISTINCT project_id FROM tasks")
                for (pid,) in cursor.fetchall():
                    cursor.execute(
                        "SELECT id FROM tasks WHERE project_id = ? "
                        "ORDER BY created_at DESC, id DESC", (pid,)
                    )
                    task_ids = [row[0] for row in cursor.fetchall()]
                    cursor.executemany(
                        "UPDATE tasks SET position = ? WHERE id = ?",
                        [(pos, tid) for pos, tid in enumerate(task_ids)]
                    )

            # --- Index for fast task look-ups by project ---
            # Without this, fetching tasks requires scanning the
            # whole tasks table.  With it, SQLite jumps straight
            # to the matching rows.
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_project_id ON tasks(project_id)"
            )

            # --- Comments table (NEW, round 6) ---
            # A comment is a short note attached to a PROJECT. Like tasks, comments
            # are deleted automatically with their project (ON DELETE CASCADE).
            # There is NO number column on purpose: the number 1, 2, 3 ... shown in
            # the app is simply the position of the comment in the list (oldest
            # first), so deleting a comment renumbers the others by itself.
            # CREATE TABLE IF NOT EXISTS is safe on an existing database: the new
            # table is added, nothing that is already stored is touched.
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS comments (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    text       TEXT    NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id)
                        REFERENCES projects (id)
                        ON DELETE CASCADE
                )
            """)
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_comment_project_id ON comments(project_id)"
            )

            conn.commit()

        except sqlite3.Error as e:
            logger.error(f"Database initialisation error: {e}")
            raise

    # ----------------------------------------------------------
    # Project operations
    # ----------------------------------------------------------

    def add_project(self, title: str, deadline: Optional[str] = None) -> int:
        """
        Insert a new project row and return its auto-generated ID.

        Raises ValueError if the title already exists (caught by
        the UNIQUE constraint on the title column).

        NEW: "deadline" is optional. Pass an ISO date string such as
        "2026-12-31", or leave it as None for "no deadline". Existing
        callers that pass only a title keep working unchanged.
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            # NEW: a new project goes to the TOP of the list, which is
            # exactly how the app behaved before manual ordering existed
            # (newest first). "Top" = one less than the current smallest
            # position; COALESCE handles the very first project (no rows yet).
            cursor.execute("SELECT COALESCE(MIN(position), 0) - 1 FROM projects")
            top_position = cursor.fetchone()[0]
            cursor.execute(
                "INSERT INTO projects (title, deadline, position) VALUES (?, ?, ?)",
                (title, deadline, top_position)
            )
            conn.commit()
            return cursor.lastrowid  # The ID assigned by SQLite

        except sqlite3.IntegrityError:
            # UNIQUE constraint fired — friendly message for the UI
            raise ValueError(f"A project named '{title}' already exists.")

        except sqlite3.Error as e:
            logger.error(f"Error adding project: {e}")
            raise

    def get_all_projects(self) -> List[Tuple]:
        """
        Return all projects as a list of (id, title) tuples,
        newest first.

        UPDATE (drag-and-drop + deadlines): the tuples are now
        (id, title, deadline) -- deadline is an ISO date string or None --
        and the order is the user's manual order (the "position" column).
        New projects are inserted at the top, so until the user drags
        anything the list still looks "newest first" like before.
        mid_frame.py is the only caller and was updated to unpack 3 values.

        UPDATE (bell / notifications): the tuples are now
        (id, title, deadline, muted); muted is 0 or 1. Still only mid_frame.py
        calls this, and it was updated to unpack 4 values.
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            # id DESC is only a tie-breaker so the order is always stable.
            cursor.execute(
                "SELECT id, title, deadline, COALESCE(muted, 0) FROM projects "
                "ORDER BY position ASC, id DESC"
            )
            return cursor.fetchall()

        except sqlite3.Error as e:
            logger.error(f"Error getting projects: {e}")
            return []

    def delete_project(self, project_id: int) -> bool:
        """
        Delete a project by ID.  Its tasks are removed automatically
        by the ON DELETE CASCADE foreign-key rule.

        Returns True if a row was actually deleted, False otherwise.
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            conn.commit()
            return cursor.rowcount > 0  # rowcount = number of rows affected

        except sqlite3.Error as e:
            logger.error(f"Error deleting project: {e}")
            return False

    def update_project_title(self, project_id: int, new_title: str) -> bool:
        """
        NEW: Rename a folder (project).

        Raises ValueError if the new title collides with another
        folder's title (UNIQUE constraint on projects.title),
        mirroring the same pattern used in add_project().
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE projects SET title = ? WHERE id = ?",
                (new_title, project_id)
            )
            conn.commit()
            return cursor.rowcount > 0

        except sqlite3.IntegrityError:
            raise ValueError(f"A folder named '{new_title}' already exists.")

        except sqlite3.Error as e:
            logger.error(f"Error renaming project: {e}")
            return False

    def update_project_deadline(self, project_id: int, deadline: Optional[str]) -> bool:
        """
        NEW: Set, change or clear (None) a project's deadline.

        The deadline is stored as an ISO "YYYY-MM-DD" text value, which
        sorts correctly and needs no special SQLite date type.
        Returns True if the project row was found and updated.
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE projects SET deadline = ? WHERE id = ?",
                (deadline, project_id)
            )
            conn.commit()
            return cursor.rowcount > 0

        except sqlite3.Error as e:
            logger.error(f"Error updating project deadline: {e}")
            return False

    def set_project_muted(self, project_id: int, muted: bool) -> bool:
        """
        NEW: Mute or un-mute the deadline reminders of one project.

        Only the launch reminders look at this flag; nothing else about a
        muted project changes. Returns True if the project row was found.
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE projects SET muted = ? WHERE id = ?",
                (1 if muted else 0, project_id)
            )
            conn.commit()
            return cursor.rowcount > 0

        except sqlite3.Error as e:
            logger.error(f"Error updating project mute flag: {e}")
            return False

    def reorder_projects(self, ordered_ids: List[int]) -> bool:
        """
        NEW: Save the order produced by drag-and-drop.

        ordered_ids is the full list of project ids from top to bottom.
        Every project is renumbered 0..n-1 in ONE transaction, so the
        order is either saved completely or not at all.
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.executemany(
                "UPDATE projects SET position = ? WHERE id = ?",
                [(pos, pid) for pos, pid in enumerate(ordered_ids)]
            )
            conn.commit()
            return True

        except sqlite3.Error as e:
            logger.error(f"Error reordering projects: {e}")
            conn.rollback()   # undo a half-finished renumbering
            return False

    def get_project_task_counts(self, project_id: int) -> Tuple[int, int]:
        """
        Return (total_tasks, completed_tasks) for a given project.

        Used to display a "3 / 5 done" progress badge on each
        project card — new feature that was missing before.
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Count all tasks for this project
            cursor.execute(
                "SELECT COUNT(*) FROM tasks WHERE project_id = ?",
                (project_id,)
            )
            total = cursor.fetchone()[0]

            # Count only the completed ones
            cursor.execute(
                "SELECT COUNT(*) FROM tasks WHERE project_id = ? AND completed = 1",
                (project_id,)
            )
            done = cursor.fetchone()[0]

            return total, done

        except sqlite3.Error as e:
            logger.error(f"Error getting task counts: {e}")
            return 0, 0

    # ----------------------------------------------------------
    # Comment operations  (NEW, round 6)
    # ----------------------------------------------------------
    # The comments of a project are shown as 1, 2, 3 ... in the order they were
    # created. That order is simply "lowest id first" -- comments cannot be
    # re-ordered -- and the number is never stored (see init_db).

    def add_comment(self, project_id: int, text: str) -> int:
        """Add a comment at the END of a project's comment list; return its id."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO comments (project_id, text) VALUES (?, ?)",
                (project_id, text)
            )
            conn.commit()
            return cursor.lastrowid

        except sqlite3.Error as e:
            logger.error(f"Error adding comment: {e}")
            raise

    def get_comments(self, project_id: int) -> List[Tuple]:
        """Return a project's comments as (id, text) tuples, oldest first."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, text FROM comments WHERE project_id = ? ORDER BY id ASC",
                (project_id,)
            )
            return cursor.fetchall()

        except sqlite3.Error as e:
            logger.error(f"Error getting comments: {e}")
            return []

    def update_comment(self, comment_id: int, text: str) -> bool:
        """Change the text of one comment. Returns True if it was found."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE comments SET text = ? WHERE id = ?", (text, comment_id)
            )
            conn.commit()
            return cursor.rowcount > 0

        except sqlite3.Error as e:
            logger.error(f"Error updating comment: {e}")
            return False

    def delete_comment(self, comment_id: int) -> bool:
        """Delete one comment. The ones after it move up by one number."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
            conn.commit()
            return cursor.rowcount > 0

        except sqlite3.Error as e:
            logger.error(f"Error deleting comment: {e}")
            return False

    # ----------------------------------------------------------
    # Task operations
    # ----------------------------------------------------------

    def add_task(self, project_id: int, description: str) -> int:
        """
        Insert a new task and return its auto-generated ID.
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            # NEW: put the new task at the TOP of its project, matching the
            # newest-first order the app had before manual ordering existed.
            cursor.execute(
                "SELECT COALESCE(MIN(position), 0) - 1 FROM tasks WHERE project_id = ?",
                (project_id,)
            )
            top_position = cursor.fetchone()[0]
            cursor.execute(
                "INSERT INTO tasks (project_id, description, position) VALUES (?, ?, ?)",
                (project_id, description, top_position)
            )
            conn.commit()
            return cursor.lastrowid

        except sqlite3.Error as e:
            logger.error(f"Error adding task: {e}")
            raise

    def get_tasks(self, project_id: int) -> List[Tuple]:
        """
        Return all tasks for a project as
        (id, description, notes, completed) tuples, newest first.

        CHANGED: "notes" added to the SELECT and to the returned
        tuple shape so the UI can show/edit task details. Any code
        that unpacks this tuple must now expect 4 values, not 3.
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, description, notes, completed
                FROM   tasks
                WHERE  project_id = ?
                ORDER  BY position ASC, id DESC
            """, (project_id,))
            # UPDATE: tasks are now sorted by the manual "position" column
            # instead of created_at. New tasks get the smallest position, so
            # the default look (newest first) is unchanged until the user drags.
            return cursor.fetchall()

        except sqlite3.Error as e:
            logger.error(f"Error getting tasks: {e}")
            return []

    def update_task(self, task_id: int, description: str, notes: str = "") -> bool:
        """
        NEW: Update a task's title (description) and/or details (notes).
        Used by the task-editing pop-up dialog.
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE tasks SET description = ?, notes = ? WHERE id = ?",
                (description, notes, task_id)
            )
            conn.commit()
            return cursor.rowcount > 0

        except sqlite3.Error as e:
            logger.error(f"Error updating task: {e}")
            return False

    def reorder_tasks(self, project_id: int, ordered_ids: List[int]) -> bool:
        """
        NEW: Save the order of ONE project's tasks after a drag-and-drop.

        ordered_ids lists that project's task ids from top to bottom. The
        "AND project_id = ?" guard means a task id from some other project
        can never be renumbered by accident.
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.executemany(
                "UPDATE tasks SET position = ? WHERE id = ? AND project_id = ?",
                [(pos, tid, project_id) for pos, tid in enumerate(ordered_ids)]
            )
            conn.commit()
            return True

        except sqlite3.Error as e:
            logger.error(f"Error reordering tasks: {e}")
            conn.rollback()
            return False

    def update_task_status(self, task_id: int, completed: bool) -> bool:
        """
        Flip a task's completed flag.

        Returns True if the row was found and updated.
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE tasks SET completed = ? WHERE id = ?",
                (completed, task_id)
            )
            conn.commit()
            return cursor.rowcount > 0

        except sqlite3.Error as e:
            logger.error(f"Error updating task: {e}")
            return False

    def delete_task(self, task_id: int) -> bool:
        """
        Delete a single task by ID.

        Returns True if the row was found and deleted.
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()
            return cursor.rowcount > 0

        except sqlite3.Error as e:
            logger.error(f"Error deleting task: {e}")
            return False

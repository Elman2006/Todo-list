# ============================================================
# main.py  —  Entry point and root window
# ============================================================
# ROOT CAUSE FIXES:
#   1. app.mainloop() is now INSIDE the __name__ guard so
#      importing this module does not open a window.
#   2. ALL grid row/column configuration for the root window
#      lives HERE — child frames no longer touch master's grid.
#   3. A single DatabaseManager is created once and shared
#      through AppController to every frame.
# ============================================================

import customtkinter as ctk
import logging
import os                                 # NEW (packaging): build the path of the window icon

from database     import DatabaseManager
# UPDATE (round 4): the header bar (title + light/dark switch) was removed, so
# TopFrame is no longer imported. top_frame.py can stay in the project unused,
# or be deleted -- nothing depends on it any more.
# from top_frame    import TopFrame
from mid_frame    import MidFrame
from bottom_frame import BottomFrame
# NEW (round 6): every colour comes from settings.py (the only file to edit to change colours).
from settings     import SEPARATOR

# Set up logging for the whole application.
# INFO level shows normal events; change to DEBUG for more detail.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)s  %(levelname)s  %(message)s"
)
logger = logging.getLogger(__name__)


# ----------------------------------------------------------
# Helper: centre the window on the screen
# ----------------------------------------------------------

def center_window(window, width: int, height: int):
    """
    Calculate the top-left corner so the window is centred on
    whichever monitor the app opens on.
    """
    screen_w = window.winfo_screenwidth()
    screen_h = window.winfo_screenheight()
    x = (screen_w - width)  // 2
    y = (screen_h - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")


# ----------------------------------------------------------
# AppController  —  message bus between frames
# ----------------------------------------------------------

class AppController:
    """
    Holds the single shared DatabaseManager and a list of
    observer frames that want to know when data changes.

    Pattern: instead of frames calling each other directly
    (tight coupling), they register with the controller and
    the controller forwards events (loose coupling).
    """

    def __init__(self, db_manager: DatabaseManager):
        self.db        = db_manager     # ONE db for the whole app
        self.observers = []             # Frames listening for events

    def add_observer(self, observer):
        """Register a frame so it receives project-change events."""
        self.observers.append(observer)

    def notify_project_added(self, project_id: int):
        """
        Called by BottomFrame after a project is saved.
        Forwards the event to every registered observer.

        Observers implement on_project_added(project_id) to react.
        Fallback: if a frame only has load_projects(), call that.
        """
        for observer in self.observers:
            if hasattr(observer, "on_project_added"):
                observer.on_project_added(project_id)
            elif hasattr(observer, "load_projects"):
                observer.load_projects()

    def notify_task_mode(self, locked: bool):
        """
        NEW (add-task lock): called by MidFrame when the user starts / stops
        typing a new task. Forwards the event to every observer that has an
        on_task_mode_changed(locked) method (BottomFrame uses it to grey out
        the Add Folder button while a task is being typed).
        """
        for observer in self.observers:
            if hasattr(observer, "on_task_mode_changed"):
                observer.on_task_mode_changed(locked)


# ----------------------------------------------------------
# TodoApp  —  the root CustomTkinter window
# ----------------------------------------------------------

class TodoApp(ctk.CTk):
    """
    Root window.  Responsibilities:
      • Set theme and colour scheme
      • Define the window's grid layout (rows + columns)
      • Instantiate all frames and wire them together
    """

    def __init__(self):
        super().__init__()

        # NEW (packaging): window + taskbar icon.
        # The icon given to PyInstaller with --icon only decorates the .exe FILE
        # (Explorer, shortcuts). The running window needs an icon of its own,
        # otherwise Windows shows CustomTkinter's default one in the title bar and
        # the taskbar. Calling iconbitmap() here, before CustomTkinter's own
        # delayed "set the default icon" step, makes CustomTkinter keep ours.
        # The try/except means a missing icon file (or a system that does not
        # support .ico files) can never stop the app from starting.
        # UPDATE (round 6): packaging was removed; app.ico simply sits next to
        # main.py. The call is still needed when running from source: without it
        # CustomTkinter shows its own default logo in the title bar.
        try:
            self.iconbitmap(os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.ico"))
        except Exception as e:
            logger.warning(f"Could not set the window icon: {e}")

        # -- Appearance ----------------------------------------
        self.current_theme = "dark"          # "dark" | "light" | "system"
        ctk.set_appearance_mode(self.current_theme)
        # UPDATE (round 4): dark mode is now ALWAYS used. There is no theme
        # switch any more and the app never saved a theme preference, so
        # nothing can override this. (The light-mode colour pairs in theme.py
        # are kept on purpose; they are simply never shown.)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")  # "blue" | "green" | "dark-blue"

        # -- Window properties ---------------------------------
        self.title("Task Manager")
        # UPDATE (round 4): minimum width raised from 650 to 800 so the folder
        # header (name + deadline + the action icons) always fits.
        self.minsize(800, 600)

        # -- Grid layout for the ROOT window -------------------
        # ROW 0: TopFrame    — header bar, fixed height
        #        (UPDATE round 4: the header bar was removed; row 0 is now empty
        #        and takes no space. The row numbers below are unchanged.)
        # ROW 1: MidFrame    — main content, EXPANDS to fill space
        # ROW 2: separator   — thin visual divider, fixed
        # ROW 3: BottomFrame — add-project bar, fixed height
        #
        # weight=1 on row 1 means it gets ALL the extra vertical
        # space when the user resizes the window.
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)   # <-- expands
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=0)
        self.grid_columnconfigure(0, weight=1)  # Single column fills width

        # -- Shared database and controller --------------------
        # ONE DatabaseManager for the whole app.
        # AppController wraps it and handles inter-frame messaging.
        db         = DatabaseManager()
        controller = AppController(db)

        # -- Instantiate frames --------------------------------
        # Order matters: controller must exist before frames use it.
        # UPDATE (round 4): header bar (title + theme switch) removed.
        # self.top_frame    = TopFrame(self, self.current_theme)
        self.mid_frame    = MidFrame(self, controller)
        self.bottom_frame = BottomFrame(self, controller)

        # -- Thin separator between MidFrame and BottomFrame ---
        ctk.CTkFrame(
            self,
            height=1,
            fg_color=SEPARATOR      # was ("gray80", "gray25"); now defined in settings.py
        ).grid(row=2, column=0, sticky="ew", padx=18, pady=0)

        # -- Register MidFrame as an observer ------------------
        # When BottomFrame adds a project it calls
        # controller.notify_project_added() → MidFrame.on_project_added()
        controller.add_observer(self.mid_frame)
        # NEW (add-task lock): BottomFrame also listens, but only for the
        # task-typing lock (it has no on_project_added, so it ignores that event).
        controller.add_observer(self.bottom_frame)

        # Close the DB connection cleanly when the window is closed
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # NEW (bell / reminders): show the deadline reminders ONCE per launch, a
        # moment after the window has appeared. The timer id is kept so it can
        # be cancelled if the window is closed before it fires.
        self._alert_job = self.after(600, self._show_launch_alerts)

    def _show_launch_alerts(self):
        """NEW: one aggregated dialog for all due, un-muted folders (see MidFrame)."""
        self._alert_job = None
        try:
            self.mid_frame.show_deadline_alerts()
        except Exception as e:
            # A reminder problem must never stop the app from starting.
            logger.error(f"Could not show deadline reminders: {e}")

    def _on_close(self):
        """Called when the user clicks the window's × button."""
        # NEW: do not leave the launch-reminder timer running.
        if getattr(self, "_alert_job", None) is not None:
            self.after_cancel(self._alert_job)
            self._alert_job = None
        logger.info("Application closing — releasing database connection.")
        # Access db through mid_frame's controller reference
        if self.mid_frame.controller:
            self.mid_frame.controller.db.close_connection()
        self.destroy()


# ----------------------------------------------------------
# Entry point guard
# ----------------------------------------------------------
# ROOT CAUSE FIX: mainloop() is now INSIDE this guard.
# Previously it was at module level, which meant importing
# main.py from another script would immediately open a window.
# ----------------------------------------------------------

if __name__ == "__main__":
    app = TodoApp()
    center_window(app, 1000, 650)
    app.mainloop()

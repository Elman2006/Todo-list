import sqlite3
import logging
# The logging module in Python is the standard way to keep track of events that happen while a program is running
from typing import List, Tuple

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self, db_path="projects.db"):
        self.db_path = db_path
        self.connection = None
        self.init_db()
    
    def get_connection(self):
        if self.connection is None:
            self.connection = sqlite3.connect(
                self.db_path, 
                check_same_thread=False,  # For tkinter applications
                timeout=10
            )
        return self.connection
    
    def close_connection(self):
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def init_db(self):
        """Initialize database with projects and tasks tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Projects table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS projects (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL UNIQUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Tasks table with foreign key
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        project_id INTEGER NOT NULL,
                        description TEXT NOT NULL,
                        completed BOOLEAN DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
                    )
                """)
                
                # Create index for better performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_project_id ON tasks(project_id)")
                conn.commit()
                
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
            raise
    
    # Project operations
    def add_project(self, title: str) -> int:
        """Add a new project and return its ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO projects (title) VALUES (?)", (title,))
                conn.commit()
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            raise ValueError(f"Project '{title}' already exists")
        except sqlite3.Error as e:
            logger.error(f"Error adding project: {e}")
            raise

    def get_projects_paginated(self, limit=50, offset=0):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, title 
                FROM projects 
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            """, (limit, offset))
            return cursor.fetchall()
    
    def get_all_projects(self) -> List[Tuple]:
        """Get all projects"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, title FROM projects ORDER BY created_at DESC")
                return cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Error getting projects: {e}")
            return []
    
    def delete_project(self, project_id: int) -> bool:
        """Delete a project and all its tasks"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Error deleting project: {e}")
            return False
    
    # Task operations
    def add_task(self, project_id: int, description: str) -> int:
        """Add a task to a project"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO tasks (project_id, description) VALUES (?, ?)",
                    (project_id, description)
                )
                conn.commit()
                return cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Error adding task: {e}")
            raise
    
    def get_tasks(self, project_id: int) -> List[Tuple]:
        """Get all tasks for a project"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, description, completed 
                    FROM tasks 
                    WHERE project_id = ? 
                    ORDER BY created_at DESC
                """, (project_id,))
                return cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Error getting tasks: {e}")
            return []
    
    def update_task_status(self, task_id: int, completed: bool) -> bool:
        """Update task completion status"""
        try:
            with self.get_connection() as conn:
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
        """Delete a task"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Error deleting task: {e}")
            return False

import customtkinter as ctk
from tkinter import messagebox
from database import DatabaseManager
import logging
import sqlite3

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BottomFrame(ctk.CTkFrame):
    def __init__(self, master, controller=None):
        super().__init__(master)
        self.grid(row=3, column=0, sticky="ew", padx=10, pady=(5, 10))
        
        # Configure grid for proper expansion
        self.grid_columnconfigure(0, weight=1)  # Entry expands

        self.db = DatabaseManager()
        self.controller = controller

        # Project entry section
        self.test_label = ctk.CTkLabel(self, text="Add new project", font=("Arial", 16, "bold"))
        self.test_label.grid(row=0, column=0, columnspan=2, pady=(5, 10))

        self.proj_ent = ctk.CTkEntry(
            self,
            placeholder_text="Enter Project's title...",
            height=35,
            font=("Arial", 16),
        )
        self.proj_ent.grid(row=1, column=0, sticky="ew", pady=5, padx=(5, 5))
        self.proj_ent.bind("<Return>", lambda e: self.add_project_btn())  # Added Enter key binding

        self.add_btn = ctk.CTkButton(
            self,
            text="Add Project",
            font=("Arial", 16),
            command=self.add_project_btn,
            width=100
        )
        self.add_btn.grid(row=1, column=1, pady=5, padx=(0, 5), sticky="e")
        
    def add_project_btn(self):
        """Add a new project"""

        # STEP 1: Get the text from the input field and clean it up
        title = self.proj_ent.get().strip()

        # STEP 2: Check if the user actually typed something
        if not title:
            messagebox.showwarning("Warning", "Please enter a project title!")
            return

        # STEP 3: Try to save the project to the database
        try:
            project_id = self.db.add_project(title)
            self.proj_ent.delete(0, "end")  # Clear the input field after saving
            
            # Use controller to notify other components
            # STEP 4: Notify other parts of the app about the new project
            if self.controller:
                self.controller.notify_project_added(project_id)
            else:
                # Fallback if controller isn't available
                # Fallback: try to call master methods if controller not available
                if hasattr(self.master, 'load_projects'):
                    self.master.load_projects()

        # STEP 5: Handle different types of errors that might occur
        except ValueError as e:
            messagebox.showerror("Error", str(e))
        
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint" in str(e):
                messagebox.showerror("Error", "Project name already exists")
            else:
                messagebox.showerror("Error", "Database integrity error")

        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            messagebox.showerror("Error", "Database operation failed")

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            messagebox.showerror("Error", "An unexpected error occurred")

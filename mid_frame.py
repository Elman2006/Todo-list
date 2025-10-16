# --------------------------- Importing the Internal and External Modules ------------------------------------------
import customtkinter as ctk
from tkinter import messagebox  # Messagebox for notifications
from database import DatabaseManager  # An Internal module to control our database
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProjectFrame(ctk.CTkFrame):
    """Frame for individual project in the projects list"""
    def __init__(self, master, title, project_id, on_select=None, on_delete=None):
        super().__init__(master)
        self.project_id = project_id
        self.on_select = on_select
        self.on_delete = on_delete
        
        # Configure grid to expand properly
        self.grid_columnconfigure(0, weight=1)

        # Project button - fills available space
        self.title_btn = ctk.CTkButton(
            self,
            text=title,
            font=("Arial", 14),
            command=self._on_select,
            anchor="w",
            fg_color="transparent",
            text_color=("black", "white"),
            hover_color=("gray70", "gray30")
        )
        self.title_btn.grid(row=0, column=0, sticky="ew", padx=(5, 0), pady=2)
        
        # Delete button - fixed width
        self.delete_btn = ctk.CTkButton(
            self,
            text="✕",
            width=30,
            height=30,
            font=("Arial", 12, "bold"),
            command=self._on_delete,
            fg_color="red",
            hover_color="darkred"
        )
        self.delete_btn.grid(row=0, column=1, padx=(5, 5), pady=2)
    
    def _on_select(self):
        if self.on_select:
            self.on_select(self.project_id)
    
    def _on_delete(self):
        if self.on_delete:
            self.on_delete(self.project_id)


class TaskFrame(ctk.CTkFrame):
    """Frame for individual task in the tasks list"""
    def __init__(self, master, task_id, description, completed, on_toggle=None, on_delete=None):
        super().__init__(master)
        self.task_id = task_id
        self.on_toggle = on_toggle
        self.on_delete = on_delete
        
        # Configure grid for proper expansion
        self.grid_columnconfigure(1, weight=1)  # Description column expands
        
        self.check_var = ctk.StringVar(value="on" if completed else "off")
        
        # Checkbox for task completion
        self.checkbox = ctk.CTkCheckBox(
            self,
            text="",
            variable=self.check_var,
            onvalue="on",
            offvalue="off",
            command=self._on_toggle,
            width=20
        )
        self.checkbox.grid(row=0, column=0, padx=(5, 5), pady=5, sticky="w")
        
        # Task description label - expands to fill space
        self.desc_label = ctk.CTkLabel(
            self,
            text=description,
            font=("Arial", 14),
            anchor="w"
        )
        self.desc_label.grid(row=0, column=1, sticky="ew", padx=(0, 5), pady=5)
        
        # Delete button - fixed width
        self.delete_btn = ctk.CTkButton(
            self,
            text="✕",
            width=30,
            height=30,
            font=("Arial", 12, "bold"),
            command=self._on_delete,
            fg_color="red",
            hover_color="darkred"
        )
        self.delete_btn.grid(row=0, column=2, padx=(5, 5), pady=5, sticky="e")
        
        # Update appearance based on completion status
        self.update_status(completed)
    
    def _on_toggle(self):
        """ toggling method """
        # Gets the toggle and if it returns true, then make complete = "on"
        if self.on_toggle:
            completed = self.check_var.get() == "on"
            self.on_toggle(self.task_id, completed)
    
    def _on_delete(self):
        if self.on_delete:
            self.on_delete(self.task_id)
    
    def update_status(self, completed):
        """Update task appearance based on completion status"""
        if completed:
            self.desc_label.configure(text_color="gray", font=("Arial", 14, "overstrike"))
        else:
            self.desc_label.configure(text_color=("black", "white"), font=("Arial", 14))


class MidFrame(ctk.CTkFrame):
    def __init__(self, master, controller=None):
        super().__init__(master)
        self.controller = controller
        self.db = controller.db if controller else DatabaseManager()
        self.current_project_id = None
        self.projects = {}
        self.task_frames = {}
        
        # Let this frame expand inside master - FIXED: removed pady to reduce gaps
        self.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 0))

        # Configure master grid weights for proper expansion
        master.grid_rowconfigure(1, weight=1)    # MidFrame row expands
        master.grid_columnconfigure(0, weight=1)  # Single column expands

        # Configure MidFrame grid for two-column layout
        self.grid_columnconfigure(0, weight=1)  # Left side (Projects) - 1 part
        self.grid_columnconfigure(1, weight=2)  # Right side (Tasks) - 2 parts (2:1 ratio)
        self.grid_rowconfigure(0, weight=1)     # Single row expands vertically

        # ---------- LEFT SIDE (Projects Section) ----------
        self.left_frame = ctk.CTkFrame(self)
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        # Configure left_frame grid: header + scrollable area
        self.left_frame.grid_rowconfigure(1, weight=1)  # Scrollable area expands
        self.left_frame.grid_columnconfigure(0, weight=1)  # Single column expands

        # Projects header
        self.topic_label = ctk.CTkLabel(
            self.left_frame, 
            text="Your Projects", 
            font=("Arial", 16, "bold")
        )
        self.topic_label.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))

        # Projects scrollable frame - DYNAMIC: fills available space
        self.projects_scroll = ctk.CTkScrollableFrame(self.left_frame)
        self.projects_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.projects_scroll.grid_columnconfigure(0, weight=1)  # Projects fill width

        # ---------- RIGHT SIDE (Tasks Section) ----------
        self.right_frame = ctk.CTkFrame(self)
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        
        # Configure right_frame grid: header + scrollable + entry
        self.right_frame.grid_rowconfigure(1, weight=1)  # Tasks area expands
        self.right_frame.grid_rowconfigure(2, weight=0)  # Entry area fixed height
        self.right_frame.grid_columnconfigure(0, weight=1)  # Single column expands

        # Project info header
        self.project_info_label = ctk.CTkLabel(
            self.right_frame, 
            text="Select a project to view tasks", 
            font=("Arial", 16, "bold"),
            height=40
        )
        self.project_info_label.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))

        # Tasks scrollable frame - DYNAMIC: fills available space
        self.tasks_scroll = ctk.CTkScrollableFrame(self.right_frame)
        self.tasks_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.tasks_scroll.grid_columnconfigure(0, weight=1)  # Tasks fill width

        # Task entry frame at bottom - fixed height
        self.task_entry_frame = ctk.CTkFrame(self.right_frame)
        self.task_entry_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
        self.task_entry_frame.grid_columnconfigure(0, weight=1)  # Entry expands

        # Task entry and button
        self.task_entry = ctk.CTkEntry(
            self.task_entry_frame,
            placeholder_text="Enter task description...",
            height=35,
            font=("Arial", 16)
        )
        self.task_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5), pady=5)
        self.task_entry.bind("<Return>", lambda e: self.add_task())

        self.add_task_btn = ctk.CTkButton(
            self.task_entry_frame,
            text="Add Task",
            font=("Arial", 16),
            command=self.add_task,
            width=80
        )
        self.add_task_btn.grid(row=0, column=1, padx=(0, 0), pady=5, sticky="e")

        # Load initial projects
        self.load_projects()

    def on_project_added(self, project_id):
        """Called when a new project is added via controller"""
        self.load_projects()
        self._select_project(project_id)

    def load_projects(self):
        """Load all projects from database"""
        projects_data = self.db.get_all_projects()
        
        # Clear existing projects
        for widget in self.projects_scroll.winfo_children():
            widget.destroy()
        
        self.projects = {}

        for project_id, title in projects_data:
            project_frame = ProjectFrame(
                self.projects_scroll,
                title,
                project_id,
                on_select=self._select_project,
                on_delete=self._delete_project
            )
            project_frame.pack(fill="x", pady=2)  # Fill horizontal space
            self.projects[project_id] = project_frame

    def _select_project(self, project_id):
        """Select a project and load its tasks"""
        self.current_project_id = project_id
        
        # Update project info label
        project_title = ""
        for pid, frame in self.projects.items():
            if pid == project_id:
                project_title = frame.title_btn.cget("text")
                break
        
        self.project_info_label.configure(text=f"Tasks for: {project_title}")
        
        # Load tasks for this project
        self._load_tasks(project_id)

    def _load_tasks(self, project_id):
        """Load tasks for the selected project"""
        # Clear existing tasks
        for widget in self.tasks_scroll.winfo_children():
            widget.destroy()
        
        self.task_frames = {}
        
        tasks_data = self.db.get_tasks(project_id)
        
        for task_id, description, completed in tasks_data:
            task_frame = TaskFrame(
                self.tasks_scroll,
                task_id,
                description,
                completed,
                on_toggle=self._toggle_task,
                on_delete=self._delete_task
            )
            task_frame.pack(fill="x", pady=2)  # Fill horizontal space
            self.task_frames[task_id] = task_frame

        # Show message if no tasks
        if not tasks_data:
            no_tasks_label = ctk.CTkLabel(
                self.tasks_scroll,
                text="No tasks yet. Add a task below!",
                font=("Arial", 14),
                text_color=("gray50", "gray70")
            )
            no_tasks_label.pack(pady=20)

    def _toggle_task(self, task_id, completed):
        """Toggle task completion status"""
        success = self.db.update_task_status(task_id, completed)
        
        if success and task_id in self.task_frames:
            self.task_frames[task_id].update_status(completed)

    def _delete_task(self, task_id):
        """Delete a task"""
        if not messagebox.askyesno(
            "Confirm Delete", 
            "Are you sure you want to delete this task?",
            icon="warning"
        ):
            return
        
        success = self.db.delete_task(task_id)
        
        if success:
            if task_id in self.task_frames:
                self.task_frames[task_id].destroy()
                del self.task_frames[task_id]
        else:
            messagebox.showerror("Error", "Failed to delete task")

    def _delete_project(self, project_id):
        """Delete a project"""
        if not messagebox.askyesno(
            "Confirm Delete", 
            "Are you sure you want to delete this project and all its tasks?",
            icon="warning"
        ):
            return
        
        success = self.db.delete_project(project_id)
        
        if success:
            if self.current_project_id == project_id:
                self.current_project_id = None
                self.project_info_label.configure(text="Select a project to view tasks")
                # Clear tasks view
                for widget in self.tasks_scroll.winfo_children():
                    widget.destroy()
                self.task_frames = {}
            self.load_projects()
            messagebox.showinfo("Success", "Project deleted successfully!")
        else:
            messagebox.showerror("Error", "Failed to delete project")

    def add_task(self):
        """Add a new task to the current project"""
        if not self.current_project_id:
            messagebox.showwarning("Warning", "Please select a project first!")
            return
        
        description = self.task_entry.get().strip()
        
        if not description:
            messagebox.showwarning("Warning", "Please enter a task description!")
            return
        
        try:
            task_id = self.db.add_task(self.current_project_id, description)
            self.task_entry.delete(0, "end")
            self._load_tasks(self.current_project_id)
            
        except Exception as e:
            logger.error(f"Error adding task: {e}")
            messagebox.showerror("Error", "Failed to add task")

# ------------------------ Importing Internal and External modules ----------------------------
import customtkinter as ctk  # Main library
from top_frame import TopFrame
from mid_frame import MidFrame
from bottom_frame import BottomFrame
from database import DatabaseManager  # An Internal module to control our database


# ------------------ Constants ------------------
def center_window(window, width, height):
    """ This is a function to centralise the window"""
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = int((screen_width / 2) - (width / 2))
    y = int((screen_height / 2) - (height / 2))
    window.geometry(f"{width}x{height}+{x}+{y}")


# ------------------ Control your database -----------------------------
class AppController:
    def __init__(self, db_manager):
        self.db = db_manager
        self.observers = []
    
    def add_observer(self, observer):
        """Add an observer to notify when projects change"""
        self.observers.append(observer)
    
    def notify_project_added(self, project_id):
        """Notify all observers that a project was added"""
        for observer in self.observers:
            if hasattr(observer, 'on_project_added'):
                observer.on_project_added(project_id)
            elif hasattr(observer, 'load_projects'):
                # Fallback: call load_projects if on_project_added not available
                observer.load_projects()


# ----------------- Main class --------------------
class TodoApp(ctk.CTk):
    """ Main class to creat the app """
    def __init__(self):
        super().__init__()

        self.current_theme = "dark"  # Options: "dark", "light", "system"

        # Configure window's title
        self.title("Project Todo Manager")

        # Set initial theme
        ctk.set_appearance_mode(self.current_theme)
        ctk.set_default_color_theme("blue")  # Options: "blue", "green", "dark-blue"

        # Initialize controller first, then frames
        self.controller = AppController(DatabaseManager())
        
        # Pass controller to all frames
        self.top_frame = TopFrame(self, self.current_theme)
        self.mid_frame = MidFrame(self, self.controller)
        self.bottom_frame = BottomFrame(self, self.controller)
        
        # Register mid_frame as observer
        self.controller.add_observer(self.mid_frame)

        self.grid_rowconfigure(0, weight=0)    # TopFrame - fixed height
        self.grid_rowconfigure(1, weight=1)    # MidFrame - expands (MOST IMPORTANT)
        self.grid_rowconfigure(2, weight=0)    # (Optional spacer if needed)
        self.grid_rowconfigure(3, weight=0)    # BottomFrame - fixed height
        
        self.grid_columnconfigure(0, weight=1)  # Single column expands


# ------------------------ run ---------------------------------
app = TodoApp()

# Set app size and center it
center_window(app, 1000, 630)
app.minsize(630, 600)

if __name__ == "__main__":
    app.mainloop()

# ============================================================
# bottom_frame.py  —  "Add new project" input bar
# ============================================================
# ROOT CAUSE FIX:
#   The original BottomFrame created its OWN DatabaseManager:
#       self.db = DatabaseManager()
#   This is a second, independent connection to the same file,
#   which can diverge from MidFrame's connection.
#   Now BottomFrame receives the shared db from the controller,
#   so the whole app uses ONE DatabaseManager instance.
# ============================================================

import customtkinter as ctk
from tkinter import messagebox
import sqlite3
import logging
from datetime import date            # NEW: type of the date returned by the calendar
from typing import Optional          # NEW: the deadline may be "nothing chosen" (None)

from calendar_popup import CalendarPopup   # NEW: themed date picker (calendar_popup.py)
from theme import (
    FONT_LG, FONT_MD,
    PAD_SM, PAD_MD, PAD_LG,
    RADIUS_BTN, RADIUS_CARD
)
# NEW (round 6): colours come from settings.py.
from settings import (
    ACCENT, ACCENT_HOVER,
    TEXT_SECONDARY, TEXT_PRIMARY,
    SURFACE_HOVER, BORDER_SUBTLE, DANGER,
    LOCKED_BG, LOCKED_TEXT        # NEW: greyed-out look while a task is being typed
)

logger = logging.getLogger(__name__)


class BottomFrame(ctk.CTkFrame):
    """
    The slim bar at the bottom of the window for adding projects.

    Layout: [  label  |  entry field (expands)  |  Add button  ]
    """

    def __init__(self, master, controller=None):
        super().__init__(master, fg_color="transparent")

        # Place this frame in row 3 (below MidFrame) of the parent grid
        self.grid(row=3, column=0, sticky="ew",
                  padx=PAD_LG, pady=(0, PAD_MD))

        self.controller = controller

        # ROOT CAUSE FIX: use the controller's shared db, not a new one
        self.db = controller.db if controller else None

        # Column layout: [label fixed] [entry expands] [button fixed]
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)
        # UPDATE: a deadline picker was inserted, so the layout is now
        # [label] [entry expands] [deadline picker] [Add button]. Column 2
        # holds the picker and the Add button moved to column 3.
        self.grid_columnconfigure(3, weight=0)

        # NEW: the deadline chosen for the NEXT project, as ISO text
        # ("2026-12-31"), or None = "no deadline" (the deadline is optional).
        self.selected_deadline: Optional[str] = None

        # NEW (add-task lock): True while the user is typing a new task. The
        # controls that add a PROJECT are then greyed out and do nothing.
        self._locked = False

        # -- Label ----------------------------------------------
        # CHANGED: "New project" -> "New folder" to match the new
        # folders/accordion concept. The underlying DB table is
        # still called "projects" (no schema rename needed).
        ctk.CTkLabel(
            self,
            text="New folder",
            font=FONT_MD,
            text_color=TEXT_SECONDARY,
            width=90
        ).grid(row=0, column=0, sticky="w",
               padx=(PAD_MD, PAD_SM), pady=PAD_SM)

        # -- Text entry -----------------------------------------
        self.proj_entry = ctk.CTkEntry(
            self,
            placeholder_text="Folder name…",
            height=38,
            font=FONT_MD,
            corner_radius=RADIUS_BTN,
            border_color=ACCENT
        )
        self.proj_entry.grid(row=0, column=1, sticky="ew",
                             padx=(0, PAD_SM), pady=PAD_SM)

        # Pressing Enter in this field is the same as clicking Add
        self.proj_entry.bind("<Return>", lambda e: self._add_project())

        # -- Optional deadline picker (NEW) ---------------------
        # A button that opens the calendar, plus a small "x" that appears
        # only while a date is chosen so it can be removed again. Leaving
        # it untouched creates a project without a deadline.
        deadline_box = ctk.CTkFrame(self, fg_color="transparent")
        deadline_box.grid(row=0, column=2, padx=(0, PAD_SM), pady=PAD_SM)

        self.deadline_btn = ctk.CTkButton(
            deadline_box,
            text="📅 Deadline",
            font=FONT_MD,
            height=38,
            width=128,
            fg_color="transparent",        # outlined style = secondary action
            border_width=1,
            border_color=BORDER_SUBTLE,
            text_color=TEXT_PRIMARY,
            hover_color=SURFACE_HOVER,
            corner_radius=RADIUS_BTN,
            command=self._open_calendar
        )
        self.deadline_btn.grid(row=0, column=0)

        self.clear_deadline_btn = ctk.CTkButton(
            deadline_box,
            text="✕",
            width=28,
            height=38,
            font=(FONT_MD[0], 11, "bold"),
            fg_color="transparent",
            text_color=DANGER,
            hover_color=SURFACE_HOVER,
            corner_radius=RADIUS_BTN,
            command=lambda: self._on_deadline_picked(None)    # None = remove it
        )
        self.clear_deadline_btn.grid(row=0, column=1, padx=(PAD_SM // 2, 0))
        self.clear_deadline_btn.grid_remove()    # hidden until a date is chosen

        # -- Add button -----------------------------------------
        self.add_btn = ctk.CTkButton(
            self,
            text="Add Folder",
            font=FONT_MD,
            height=38,
            width=110,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            corner_radius=RADIUS_BTN,
            command=self._add_project
        )
        self.add_btn.grid(row=0, column=3, pady=PAD_SM)   # was column 2

        # NEW (add-task lock): MidFrame's click handler looks for this flag on a
        # clicked widget; True means "greyed out, ignore the click".
        self.add_btn.lock_active = False
        self.deadline_btn.lock_active = False
        self.clear_deadline_btn.lock_active = False

    # ----------------------------------------------------------
    # Deadline picker (NEW)
    # ----------------------------------------------------------

    def on_task_mode_changed(self, locked: bool):
        """
        NEW: called (through AppController.notify_task_mode) when the user starts
        or stops typing a new task.

        While locked, the controls that add a project -- the Add Folder button
        and the deadline picker with its x -- are greyed out and do nothing. The
        folder-name entry itself stays usable: clicking into it simply ends the
        task-typing mode and everything is enabled again.
        """
        self._locked = locked
        for button in (self.add_btn, self.deadline_btn, self.clear_deadline_btn):
            button.lock_active = locked
            button.configure(state="disabled" if locked else "normal")

        if locked:
            self.add_btn.configure(fg_color=LOCKED_BG, text_color_disabled=LOCKED_TEXT)
            self.deadline_btn.configure(border_color=LOCKED_BG, text_color_disabled=LOCKED_TEXT)
            self.clear_deadline_btn.configure(text_color_disabled=LOCKED_TEXT)
        else:
            self.add_btn.configure(fg_color=ACCENT)
            self.deadline_btn.configure(border_color=BORDER_SUBTLE)

    def _open_calendar(self):
        """Open the calendar below the Deadline button (pre-set to the current choice)."""
        if self._locked:             # NEW (add-task lock): do nothing while a task is being typed
            return
        initial = None
        if self.selected_deadline:
            initial = date.fromisoformat(self.selected_deadline)   # we stored it ourselves, so it is valid
        CalendarPopup(
            self.winfo_toplevel(),
            initial=initial,
            on_select=self._on_deadline_picked,
            anchor=self.deadline_btn
        )

    def _on_deadline_picked(self, chosen: Optional[date]):
        """
        Called with a date (picked), or None (cleared / reset after saving).
        Remembers the choice as ISO text and updates the button's label.
        """
        if chosen is None:
            self.selected_deadline = None
            self.deadline_btn.configure(text="📅 Deadline")
            self.clear_deadline_btn.grid_remove()         # nothing to clear any more
        else:
            self.selected_deadline = chosen.isoformat()
            self.deadline_btn.configure(text=f"📅 {self.selected_deadline}")
            self.clear_deadline_btn.grid()                # show the "x"

    # ----------------------------------------------------------
    # Action handler
    # ----------------------------------------------------------

    def _add_project(self):
        """
        Read the entry field, validate, save to DB, notify other
        frames via the controller, then clear and re-focus the field.

        STEP 1 → get + clean input text
        STEP 2 → guard against empty input
        STEP 3 → save to database (uses controller's shared db)
        STEP 4 → notify MidFrame via AppController
        STEP 5 → restore focus so the user can type the next project
        STEP 6 → handle all possible error types explicitly
        """

        # NEW (add-task lock): while a task is being typed this does nothing.
        if self._locked:
            return

        # STEP 1: Get text and strip surrounding whitespace
        title = self.proj_entry.get().strip()

        # STEP 2: Reject blank input immediately
        if not title:
            messagebox.showwarning("Warning", "Please enter a folder name.")
            self.proj_entry.focus_set()
            return

        # STEP 3: Write to the database
        try:
            # NEW: the optional deadline is saved together with the title.
            project_id = self.db.add_project(title, self.selected_deadline)

            # Clear the input field right after a successful save
            self.proj_entry.delete(0, "end")

            # NEW: forget the chosen deadline so the NEXT project starts with
            # none (otherwise every project would silently inherit it).
            self._on_deadline_picked(None)

            # STEP 4: Tell AppController → it forwards to MidFrame
            # MidFrame.on_project_added() refreshes the list and
            # auto-selects the new project.
            if self.controller:
                self.controller.notify_project_added(project_id)

            # STEP 5: Put focus back in the entry so the user can
            # immediately type another project without clicking
            self.proj_entry.focus_set()

        # STEP 6: Handle specific error types with clear messages

        except ValueError as e:
            # ValueError is raised by db.add_project() when the
            # project title already exists (UNIQUE constraint)
            messagebox.showerror("Duplicate name", str(e))

        except sqlite3.IntegrityError as e:
            # Fallback in case the ValueError wrapper was bypassed
            if "UNIQUE constraint" in str(e):
                messagebox.showerror("Duplicate name",
                                     "A project with that name already exists.")
            else:
                messagebox.showerror("Database error",
                                     "A database integrity error occurred.")

        except sqlite3.Error as e:
            logger.error(f"Database error while adding project: {e}")
            messagebox.showerror("Database error",
                                 "Could not save the project. Please try again.")

        except Exception as e:
            logger.error(f"Unexpected error while adding project: {e}")
            messagebox.showerror("Error", "An unexpected error occurred.")

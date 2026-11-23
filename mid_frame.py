# ============================================================
# mid_frame.py  —  Folder accordion (collapsible projects + tasks)
# ============================================================
# WHAT CHANGED AND WHY (feature request: foldable folders,
# inline editing, modern polish):
#
#   • The old two-column "Project list | Task list" layout is
#     replaced with a SINGLE-COLUMN ACCORDION. Each folder is a
#     FolderCard; clicking its header expands/collapses its own
#     task list directly underneath. This is the only way to get
#     true "collapsed = just the name visible" behaviour, so the
#     two-column split had to go.
#   • FolderCard and TaskRow each gained a "..." menu button AND
#     a right-click binding, both opening the same tk.Menu with
#     Rename/Edit + Delete -- satisfies "two ways to trigger
#     editing" from the request.
#   • Renaming a folder and editing a task open a small modal
#     dialog (EditDialog) rather than raw inline text-replacement,
#     because folder titles must stay unique (DB constraint) and
#     tasks now have two editable fields (title + details).
#   • Hover colour swaps on folder headers and task rows give the
#     "modern feel" requested. NOTE: CustomTkinter has no built-in
#     smooth colour animation, so this is an immediate colour
#     swap on <Enter>/<Leave>, not a gradual fade -- a deliberate,
#     low-risk choice rather than hand-rolling a tween loop.
#   • Everything NOT related to folders/editing/polish (DB call
#     patterns, controller wiring, error handling style) is kept
#     identical to your working version.
# ============================================================
# ROUND 3 ADDITIONS (drag-and-drop ordering + deadlines):
#
#   • DragHandle (new class): a small "≡" label placed next to every
#     folder name and every task. Pressing and dragging it moves that
#     card up/down LIVE; releasing the mouse saves the new order to
#     SQLite through MidFrame.reorder_folders / reorder_tasks.
#     Tasks can be reordered inside their own folder only.
#   • Deadline cell on every FolderCard header: shows the date and a
#     "days left" line (see describe_deadline below). Clicking it, or
#     choosing "Edit deadline…" in the folder menu, opens the themed
#     CalendarPopup (calendar_popup.py).
#   • "Days left" is recalculated every time the list is built (app
#     start / reload) and once more by MidFrame._check_new_day when
#     midnight passes while the app stays open.
#   • Renaming a folder / editing a task already existed (right-click
#     or the "•••" button) and is unchanged.
# ============================================================
# ROUND 4 ADDITIONS (icons, status colours, preview, copy):
#
#   • The "•••" buttons are gone. Folders now show calendar / pen / trash
#     icons, tasks show copy / pen / trash icons (IconButton in icons.py,
#     Lucide icons). Right-click menus and double-click still work.
#   • The folder header is coloured by completion: green = every task done,
#     orange = some done, red = none done, neutral grey = no tasks at all
#     (see completion_status / STATUS_PALETTES / FolderCard.apply_status).
#   • A task with details shows a short preview after its title (see
#     build_preview): the first 6 whole words, plus "…" when it is longer.
#   • The copy icon puts "title, blank line, details" on the clipboard and
#     flashes a green check for a moment (TaskRow._copy).
#   • The Edit/Rename dialog is larger.
# ============================================================
# ROUND 4, BATCH 2 (add-task lock, bell + reminders):
#
#   • The "New task…" bar of each folder is now at the TOP of its task list.
#   • "Adding a task" mode: while a folder's task entry has keyboard focus AND
#     contains text, the project-level controls are DISABLED (greyed out, a
#     click does nothing): the "Add Folder" bar (see bottom_frame.py) and each
#     folder's calendar / pen / trash icons, right-click menu and double-click
#     rename. It ends when the entry loses focus, is emptied, Esc is pressed
#     or the task is submitted. Pure runtime state -- nothing is saved.
#     (FolderCard._update_task_mode -> MidFrame.set_task_mode -> _apply_lock.)
#   • Bell icon per folder: click = mute / un-mute that folder's deadline
#     reminders (saved in SQLite). On every launch ONE dialog lists all
#     folders that are due within 7 days or overdue, most urgent first
#     (collect_deadline_alerts / format_deadline_alerts / show_deadline_alerts).
# ============================================================
# ROUND 6 (comments, settings.py):
#
#   • Every colour now comes from settings.py (see the import below). The red /
#     orange / green header colour-coding can be switched off there with one
#     flag (STATUS_COLORS_ENABLED); completion_status() honours it.
#   • COMMENTS: each project has an optional list of numbered comments at the
#     TOP of its open accordion, above the "New task…" bar and the tasks
#     (CommentRow, FolderCard.refresh_comments / _add_comment, and the
#     MidFrame.add_comment / edit_comment / delete_comment methods).
#       - Nothing at all is shown for a project without comments.
#       - The "Add Comment" button creates an empty comment at the END of the
#         list, ready to be typed into right there (inline editing).
#       - The number is NOT stored: it is the position in the list. So deleting
#         a comment renumbers the ones after it, and comments cannot be moved.
#       - Comments are saved in SQLite (the comments table in database.py).
# ============================================================

import customtkinter as ctk
import tkinter as tk                 # Needed for tk.Menu -- CTk has no native menu widget
from tkinter import messagebox
from datetime import date            # NEW: today's date + deadline maths
from typing import Optional          # NEW: type hints for "may be None" values
from database import DatabaseManager
from calendar_popup import CalendarPopup   # NEW: themed date picker (calendar_popup.py)
from icons import IconButton               # NEW: rounded icon button (icons.py, Lucide icons)
from theme import (
    FONT_LG, FONT_MD, FONT_SM,
    FONT_DEADLINE, FONT_DEADLINE_BOLD,       # NEW: larger deadline text
    FONT_MENU_BTN, FONT_MENU_LIST,           # NEW: larger "•••" button + menu list
    MENU_BTN_WIDTH, MENU_BTN_HEIGHT,         # NEW: bigger "•••" click target
    FONT_COMMENT,                            # NEW (round 6): italic font of the comments
    TRANSPARENT,
    PAD_XS, PAD_SM, PAD_MD, PAD_LG,
    RADIUS_BTN, RADIUS_CARD, RADIUS_LG
)
# NEW (round 6): every colour comes from settings.py (the one file to edit to
# change colours or to switch the status colour-coding off).
from settings import (
    ACCENT, ACCENT_HOVER,
    DANGER, DANGER_HOVER,
    SUCCESS,                                 # NEW: green check after "copy"
    TEXT_PRIMARY, TEXT_SECONDARY,
    SURFACE, SURFACE_HOVER, SURFACE_SELECTED,
    BORDER_SUBTLE, ICON_MUTED, HEADER_HOVER,
    ICON_IDLE, ICON_ON_BAND, ICON_ON_BAND_HOVER, ICON_DANGER_ON_BAND_HOVER,   # NEW: icon colours
    DANGER_SOFT,                                                              # NEW: soft red hover for trash
    STATUS_DONE_BG, STATUS_DONE_HOVER, STATUS_SOME_BG, STATUS_SOME_HOVER,     # NEW: header status colours
    STATUS_NONE_BG, STATUS_NONE_HOVER,
    STATUS_TEXT, STATUS_TEXT_MUTED, STATUS_OVERDUE_TEXT,
    ICON_DIM_ON_BAND, ICON_DIM,                                               # NEW: muted-bell colours
    STATUS_COLORS_ENABLED, COMMENT_TEXT, COMPLETED_TASK_TEXT,                 # NEW (round 6)
    CHECKMARK, MENU_ACTIVE_TEXT
)
import logging

logger = logging.getLogger(__name__)


# ==============================================================
# Deadline helpers  (NEW)
# ==============================================================

def parse_deadline(iso_text) -> Optional[date]:
    """
    Turn the text stored in SQLite ("2026-12-31") into a date object.

    Returns None when there is no deadline OR when the stored text is
    not a valid date (for example if the database file was edited by
    hand). A bad value therefore behaves like "no deadline" instead of
    crashing the whole project list.
    """
    if not iso_text:
        return None
    try:
        return date.fromisoformat(str(iso_text))
    except ValueError:
        return None


def describe_deadline(iso_text):
    """
    Build the two lines shown in the Deadline cell.

    Returns (date_line, days_line, is_overdue), for example:
        ("2026-12-31", "18 days left", False)
        ("2026-11-10", "3 days overdue", True)
        ("—", "", False)            <- project has no deadline
    "Days left" is computed from today's date every time this is called,
    so it is always up to date when the list is (re)built.
    """
    deadline = parse_deadline(iso_text)
    if deadline is None:
        return "—", "", False

    days = (deadline - date.today()).days
    if days > 1:
        text = f"{days} days left"
    elif days == 1:
        text = "1 day left"
    elif days == 0:
        text = "Due today"
    elif days == -1:
        text = "1 day overdue"
    else:
        text = f"{-days} days overdue"

    return deadline.isoformat(), text, days < 0


# ==============================================================
# Three-dots menu helpers  (NEW -- polish round)
# ==============================================================

def _style_menu_button(button):
    """
    Give a "•••" button a hover state that matches the app theme.

    The button already has rounded corners and a soft accent-tinted hover
    background (set where it is created). CustomTkinter buttons cannot change
    their TEXT colour on hover by themselves, so the dots are tinted with the
    accent colour here while the pointer is over the button, and go back to
    the muted icon colour when it leaves. bind() on a CTk widget ADDS to the
    built-in hover handling instead of replacing it.
    """
    button.bind("<Enter>", lambda e: button.configure(text_color=ACCENT))
    button.bind("<Leave>", lambda e: button.configure(text_color=ICON_MUTED))


def _new_menu(parent):
    """
    Create the drop-down list shown by "•••" / right-click (Edit / Rename / Delete).

    It stays a native tk.Menu on purpose: CustomTkinter has no themed menu
    widget, and on Windows the menu's colours and corners are drawn by the
    system and cannot be changed. What CAN be changed is the font, which is
    enlarged here so the entries are easier to read and hit. The accent
    highlight is applied where the platform allows it (it is ignored on
    Windows, harmless there).
    """
    return tk.Menu(
        parent, tearoff=0,
        font=FONT_MENU_LIST,
        activebackground=ACCENT, activeforeground=MENU_ACTIVE_TEXT
    )


# ==============================================================
# Preview + status helpers  (NEW -- round 4)
# ==============================================================

# How many whole words of a task's details are shown next to its title.
PREVIEW_WORDS = 6


def build_preview(notes, max_words: int = PREVIEW_WORDS) -> str:
    """
    Build the short preview shown after a task's title.

    - No details (or only blanks/newlines)  -> "" (nothing is shown)
    - Up to max_words words                 -> the whole text, no "…"
    - More than max_words words             -> the first max_words WHOLE
      words followed by "…" (the text is split on spaces, so a word is
      never cut in half)
    Line breaks are treated like spaces, so multi-line details still give
    a one-line preview.
    """
    words = (notes or "").split()
    if not words:
        return ""
    if len(words) <= max_words:
        return " ".join(words)
    return " ".join(words[:max_words]) + "…"


def completion_status(total: int, done: int) -> str:
    """
    Decide which colour a folder header gets, from its task counts.
    "Done" means the task's existing completed flag is set.

      no tasks at all        -> "empty"  (neutral grey, as before)
      every task done        -> "done"   (green)
      at least one, not all  -> "some"   (orange)
      none done              -> "none"   (red)
    """
    # NEW (round 6): one flag in settings.py switches the colour-coding off; every
    # project then keeps the neutral header, exactly like a project without tasks.
    if not STATUS_COLORS_ENABLED:
        return "empty"
    if total == 0:
        return "empty"
    if done >= total:
        return "done"
    if done == 0:
        return "none"
    return "some"


def _band(bg, hover, text, muted, glyph, overdue, icon, icon_hover, trash_hover):
    """Small helper: one named colour set for a header state."""
    return {"bg": bg, "hover": hover, "text": text, "muted": muted, "glyph": glyph,
            "overdue": overdue, "icon": icon, "icon_hover": icon_hover,
            "trash_hover": trash_hover}


# One colour set per status. The three coloured ones share the same text and
# icon colours (light on dark muted backgrounds); "empty" keeps the colours the
# header always had, so a folder without tasks looks exactly as before.
STATUS_PALETTES = {
    "done":  _band(STATUS_DONE_BG, STATUS_DONE_HOVER, STATUS_TEXT, STATUS_TEXT_MUTED,
                   STATUS_TEXT_MUTED, STATUS_OVERDUE_TEXT, ICON_ON_BAND,
                   ICON_ON_BAND_HOVER, ICON_DANGER_ON_BAND_HOVER),
    "some":  _band(STATUS_SOME_BG, STATUS_SOME_HOVER, STATUS_TEXT, STATUS_TEXT_MUTED,
                   STATUS_TEXT_MUTED, STATUS_OVERDUE_TEXT, ICON_ON_BAND,
                   ICON_ON_BAND_HOVER, ICON_DANGER_ON_BAND_HOVER),
    "none":  _band(STATUS_NONE_BG, STATUS_NONE_HOVER, STATUS_TEXT, STATUS_TEXT_MUTED,
                   STATUS_TEXT_MUTED, STATUS_OVERDUE_TEXT, ICON_ON_BAND,
                   ICON_ON_BAND_HOVER, ICON_DANGER_ON_BAND_HOVER),
    "empty": _band(SURFACE, HEADER_HOVER, TEXT_PRIMARY, TEXT_SECONDARY,
                   ICON_MUTED, DANGER, ICON_IDLE, ACCENT, DANGER),
}

# NEW (bell): the colour of a MUTED bell (the bell with a slash) on each header.
for _status_name in ("done", "some", "none"):
    STATUS_PALETTES[_status_name]["icon_dim"] = ICON_DIM_ON_BAND
STATUS_PALETTES["empty"]["icon_dim"] = ICON_DIM


def _pointer_inside(widget) -> bool:
    """
    True if the mouse pointer is currently over `widget` or any widget
    inside it. Used so a folder header does not lose its hover colour just
    because the pointer moved onto one of its own icons (tkinter reports
    that as "leaving" the header).
    """
    try:
        x, y = widget.winfo_pointerxy()
        under = widget.winfo_containing(x, y)
    except (tk.TclError, KeyError):
        return False
    while under is not None:
        if under is widget:
            return True
        under = getattr(under, "master", None)
    return False


# ==============================================================
# Deadline reminders  (NEW -- round 4, batch 2)
# ==============================================================

ALERT_WARNING_DAYS = 7     # remind when this many days or fewer are left
ALERT_ERROR_DAYS   = 2     # "error" level at this many days or fewer (overdue is always error)
ALERT_MAX_LINES    = 12    # at most this many projects are listed; the rest become "…and N more"


def collect_deadline_alerts(projects, today=None):
    """
    Work out which projects need a reminder.

    `projects` are the rows from DatabaseManager.get_all_projects():
    (id, title, deadline, muted).

    A project is included when
      - it is NOT muted,
      - it has a (valid) deadline, and
      - 7 days or fewer are left (an overdue deadline has negative days left).
    Level: "error" for 2 days or fewer, overdue included; otherwise "warning".

    The result is sorted MOST URGENT FIRST: the most overdue project comes
    first, then those due today, and so on up to 7 days. Ties are sorted by name.
    """
    today = today or date.today()
    alerts = []
    for _project_id, title, deadline, muted in projects:
        if muted:
            continue                                   # muted projects are never reminded
        due = parse_deadline(deadline)
        if due is None:
            continue                                   # no deadline (or an unreadable one)
        days = (due - today).days
        if days > ALERT_WARNING_DAYS:
            continue
        alerts.append({
            "title": title,
            "days": days,
            "deadline": due.isoformat(),
            "text": describe_deadline(due.isoformat())[1],     # e.g. "3 days overdue"
            "level": "error" if days <= ALERT_ERROR_DAYS else "warning",
        })
    alerts.sort(key=lambda alert: (alert["days"], alert["title"].lower()))
    return alerts


def format_deadline_alerts(alerts):
    """
    Turn the alert list into ONE message for a single dialog box.

    Returns (dialog_title, message, level). `level` is "error" when at least
    one project is overdue or due within 2 days, otherwise "warning"; it
    decides which message-box icon is used. The projects are grouped under
    two headings and keep the most-urgent-first order.
    """
    urgent = [a for a in alerts if a["level"] == "error"]
    soon = [a for a in alerts if a["level"] == "warning"]

    lines = []
    shown = 0

    def add_section(heading, items):
        nonlocal shown
        if not items or shown >= ALERT_MAX_LINES:
            return
        if lines:
            lines.append("")                           # blank line between the two sections
        lines.append(heading)
        for alert in items:
            if shown >= ALERT_MAX_LINES:
                break
            lines.append(f"   •  {alert['title']}  —  {alert['text']}  ({alert['deadline']})")
            shown += 1

    add_section(f"OVERDUE OR DUE WITHIN {ALERT_ERROR_DAYS} DAYS", urgent)
    add_section(f"DUE WITHIN {ALERT_WARNING_DAYS} DAYS", soon)

    hidden = len(alerts) - shown
    if hidden > 0:
        lines.append("")
        lines.append(f"…and {hidden} more.")

    count = len(alerts)
    intro = (f"{count} project needs attention." if count == 1
             else f"{count} projects need attention.")
    level = "error" if urgent else "warning"
    return "Deadline reminders", intro + "\n\n" + "\n".join(lines), level


# ==============================================================
# EditDialog  --  small modal pop-up reused for rename + edit-task
# ==============================================================

class EditDialog(ctk.CTkToplevel):
    """
    Reusable modal dialog.

    - Renaming a folder    -> pass notes=None  (title field only)
    - Editing a task       -> pass notes=""    (title + details box)

    on_save(new_title, new_notes) is called only if the user
    confirms with a non-empty title. new_notes is None when this
    dialog was used in "folder rename" mode.
    """

    def __init__(self, master, dialog_title, initial_title,
                 initial_notes=None, on_save=None):
        super().__init__(master)
        self.title(dialog_title)
        self.resizable(False, False)
        self.on_save = on_save

        # Modal behaviour: block interaction with the main window
        # until this dialog is closed.
        self.transient(master)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)

        # -- Title field (used for both folder name and task title) --
        ctk.CTkLabel(
            self, text="Title", font=FONT_SM, text_color=TEXT_SECONDARY
        ).grid(row=0, column=0, sticky="w", padx=PAD_LG, pady=(PAD_LG, PAD_XS))

        self.title_entry = ctk.CTkEntry(
            self, font=FONT_MD, corner_radius=RADIUS_BTN,
            border_color=ACCENT, width=400   # UPDATE (round 4): was 280 -- dialog made larger
        )
        self.title_entry.insert(0, initial_title)
        self.title_entry.grid(row=1, column=0, sticky="ew",
                              padx=PAD_LG, pady=(0, PAD_SM))
        self.title_entry.focus_set()
        self.title_entry.select_range(0, "end")   # Pre-select for quick overtype

        # -- Optional details box (task editing only) --
        self.notes_box = None
        if initial_notes is not None:
            ctk.CTkLabel(
                self, text="Details (optional)", font=FONT_SM,
                text_color=TEXT_SECONDARY
            ).grid(row=2, column=0, sticky="w", padx=PAD_LG, pady=(PAD_SM, PAD_XS))

            self.notes_box = ctk.CTkTextbox(
                self, font=FONT_MD, corner_radius=RADIUS_BTN, height=160, width=400   # UPDATE (round 4): was 90 x 280
            )
            self.notes_box.insert("1.0", initial_notes)
            self.notes_box.grid(row=3, column=0, sticky="ew",
                                padx=PAD_LG, pady=(0, PAD_SM))

        # -- Save / Cancel buttons --
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.grid(row=4, column=0, sticky="e", padx=PAD_LG, pady=(PAD_SM, PAD_LG))

        ctk.CTkButton(
            btn_row, text="Cancel", width=80,
            fg_color=TRANSPARENT, text_color=TEXT_SECONDARY,
            hover_color=SURFACE_HOVER, corner_radius=RADIUS_BTN,
            command=self.destroy
        ).pack(side="left", padx=(0, PAD_SM))

        ctk.CTkButton(
            btn_row, text="Save", width=80,
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            corner_radius=RADIUS_BTN, command=self._save
        ).pack(side="left")

        # Enter = Save, Escape = Cancel (fits the entry-field muscle
        # memory used everywhere else in this app)
        self.bind("<Return>", lambda e: self._save())
        self.bind("<Escape>", lambda e: self.destroy())

    def _save(self):
        new_title = self.title_entry.get().strip()
        if not new_title:
            messagebox.showwarning("Warning", "Title cannot be empty.", parent=self)
            return
        new_notes = self.notes_box.get("1.0", "end").strip() if self.notes_box else None
        if self.on_save:
            self.on_save(new_title, new_notes)
        self.destroy()


# ==============================================================
# DragHandle  --  the "≡" grip used to reorder folders and tasks  (NEW)
# ==============================================================

class DragHandle(ctk.CTkLabel):
    """
    A small "≡" grip. Press it, move the mouse, release.

    How it works (tkinter has no built-in drag-and-drop for widgets, so
    this is done with three mouse events):
      1. <ButtonPress-1>   remember the current order, outline the card.
      2. <B1-Motion>       (mouse moves while the button is held)
                           move the card above/below its neighbours so it
                           follows the pointer. Only the on-screen order
                           changes here; nothing is saved yet.
      3. <ButtonRelease-1> if the order changed, call on_drop(cards) once
                           so the caller can save the new order to SQLite.

    "card" is the widget that moves (a FolderCard or a TaskRow). It is
    reordered only among its siblings of the same class in the same
    container, which is why tasks can never jump into another folder.
    """

    EDGE_ZONE = 36     # px from the top/bottom of the visible list where auto-scroll starts
    TICK_MS = 40       # how often auto-scroll is checked while dragging

    def __init__(self, master, card, on_drop):
        super().__init__(
            master,
            text="≡",                          # three horizontal lines
            width=22,
            font=(FONT_MD[0], 16, "bold"),
            text_color=ICON_MUTED,
            cursor="fleur"                     # four-arrow "move" cursor
        )
        self.card = card                       # the widget that gets moved
        self.on_drop = on_drop                 # called with the new top-to-bottom list of cards
        self._dragging = False
        self._start_order = []                 # card order when the drag began
        self._last_y = 0                       # last pointer height on SCREEN (y_root)
        self._tick_job = None                  # id of the pending auto-scroll timer
        self._saved_border = None              # card outline to restore after the drag

        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_motion)
        self.bind("<ButtonRelease-1>", self._on_release)

    # ----------------------------------------------------------
    # Mouse events
    # ----------------------------------------------------------

    def _on_press(self, event):
        self._dragging = True
        self._start_order = self._cards()
        self._last_y = event.y_root

        # Outline the card in the accent colour so the user can see what is
        # being dragged. The old outline is saved and put back in _stop().
        self._saved_border = (self.card.cget("border_width"), self.card.cget("border_color"))
        self.card.configure(border_width=2, border_color=ACCENT)

        self._tick_job = self.after(self.TICK_MS, self._tick)

    def _on_motion(self, event):
        if not self._dragging:
            return
        self._last_y = event.y_root
        self._reposition()

    def _on_release(self, event):
        if not self._dragging:
            return
        self._stop()
        new_order = self._cards()
        # Save only if the order really changed (a plain click does nothing).
        if new_order != self._start_order and self.on_drop:
            self.on_drop(new_order)

    # ----------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------

    def _cards(self):
        """
        All cards of the same kind in the same container, top to bottom
        (including the one being dragged). pack_info()["in"] is the
        container the card is packed into.
        """
        container = self.card.pack_info()["in"]
        return [w for w in container.pack_slaves() if isinstance(w, type(self.card))]

    def _reposition(self):
        """
        Move the card to where the pointer is.

        Rule: put the card directly above the first OTHER card whose
        vertical centre is below the pointer; if there is none, put it
        at the very end. pack_configure(before=/after=) re-orders the
        widgets without hiding them, so the mouse grab is never lost.
        """
        cards = self._cards()
        others = [w for w in cards if w is not self.card]
        if not others:
            return

        target = None
        for w in others:
            if w.winfo_rooty() + w.winfo_height() / 2 > self._last_y:
                target = w
                break

        if target is not None:
            # Skip the call when the card already sits directly above target.
            if cards.index(target) != cards.index(self.card) + 1:
                self.card.pack_configure(before=target)
        elif cards[-1] is not self.card:
            self.card.pack_configure(after=others[-1])

        # Let tkinter recalculate positions now, so the next mouse event
        # compares against up-to-date coordinates (prevents jitter).
        self.update_idletasks()

    def _tick(self):
        """Timer: scroll the list while the pointer is near its top/bottom edge."""
        self._tick_job = None
        if not self._dragging:
            return
        if self._auto_scroll():
            self._reposition()               # content moved under the pointer
        self._tick_job = self.after(self.TICK_MS, self._tick)

    def _auto_scroll(self) -> bool:
        """
        Scroll the surrounding CTkScrollableFrame one step when the pointer
        is within EDGE_ZONE px of its top or bottom. Returns True if it
        scrolled. CTkScrollableFrame has no public scroll method, so this
        uses its inner canvas (_parent_canvas); if a future CTk version
        renames it, auto-scroll quietly stops working but dragging still does.
        """
        scroll = self.card
        while scroll is not None and not isinstance(scroll, ctk.CTkScrollableFrame):
            scroll = scroll.master
        if scroll is None:
            return False
        try:
            canvas = scroll._parent_canvas
            top = canvas.winfo_rooty()
            bottom = top + canvas.winfo_height()
            first, last = canvas.yview()          # visible part of the content, 0.0 .. 1.0
            if self._last_y < top + self.EDGE_ZONE and first > 0.0:
                canvas.yview_scroll(-1, "units")
                return True
            if self._last_y > bottom - self.EDGE_ZONE and last < 1.0:
                canvas.yview_scroll(1, "units")
                return True
        except (AttributeError, tk.TclError):
            pass
        return False

    def _stop(self):
        """End the drag: stop the timer and restore the card's outline."""
        self._dragging = False
        if self._tick_job is not None:
            self.after_cancel(self._tick_job)
            self._tick_job = None
        if self._saved_border is not None:
            width, colour = self._saved_border
            # cget returns a colour PAIR as a list; configure wants a tuple.
            if isinstance(colour, list):
                colour = tuple(colour)
            try:
                self.card.configure(border_width=width, border_color=colour)
            except tk.TclError:
                pass                          # card was destroyed during the drag
            self._saved_border = None

    def destroy(self):
        """Make sure no timer is left running when the handle is removed."""
        if self._tick_job is not None:
            try:
                self.after_cancel(self._tick_job)
            except tk.TclError:
                pass
            self._tick_job = None
        super().destroy()


# ==============================================================
# TaskRow  --  one task line inside an expanded folder
# ==============================================================

class TaskRow(ctk.CTkFrame):
    """
    A single task row with:
      - Checkbox (toggles completion)
      - Description label -- double-click OR "..." OR right-click -> edit
      - "..." menu button -> Edit / Delete

    UPDATE (drag-and-drop): a "≡" DragHandle now sits at the far left.
    Grid columns are therefore: 0 handle | 1 checkbox | 2 description
    (expands) | 3 "..." menu.

    UPDATE (icons round): the "..." menu button was replaced by three icon
    buttons, so the columns are now: 0 handle | 1 checkbox | 2 title +
    details preview (expands) | 3 copy | 4 pen (edit) | 5 trash (delete).
    """

    def __init__(self, master, midframe, project_id, task_id,
                 description, notes, completed):
        super().__init__(master, fg_color=SURFACE, corner_radius=RADIUS_CARD)

        self.midframe    = midframe          # Back-reference for DB actions
        self.project_id  = project_id
        self.task_id     = task_id
        self.description = description
        self.notes       = notes or ""

        self.grid_columnconfigure(1, weight=1)
        # UPDATE: the handle took column 0, so the stretchy column is now the
        # description label in column 2 (the line above is kept for reference;
        # the next line is the one that now matters).
        self.grid_columnconfigure(2, weight=1)
        self.grid_columnconfigure(1, weight=0)

        # -- Drag handle (NEW) --------------------------------------------
        # Dragging it re-orders this task among the other tasks of the same
        # folder; _on_dropped (below) saves the result.
        self.drag_handle = DragHandle(self, card=self, on_drop=self._on_dropped)
        self.drag_handle.grid(row=0, column=0, padx=(PAD_SM, 0), pady=PAD_SM)

        # -- Checkbox -----------------------------------------------------
        self.check_var = ctk.StringVar(value="on" if completed else "off")
        self.checkbox = ctk.CTkCheckBox(
            self, text="", variable=self.check_var,
            onvalue="on", offvalue="off",
            command=self._on_toggle,
            checkbox_width=20, checkbox_height=20,
            checkmark_color=CHECKMARK,
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            border_color=TEXT_SECONDARY, width=20
        )
        self.checkbox.grid(row=0, column=1, padx=(PAD_XS, PAD_SM), pady=PAD_SM)   # was column 0

        # -- Description label ---------------------------------------------
        # UPDATE (icons round): the title and a small preview of the task's
        # details now sit side by side in one container (text_box), so the
        # preview appears right after the title. The title label is still
        # called desc_label, so everything that uses it keeps working.
        # The original lines are kept below as comments for reference.
        self.text_box = ctk.CTkFrame(self, fg_color="transparent")
        self.text_box.grid(row=0, column=2, sticky="ew", padx=(0, PAD_SM), pady=PAD_SM)

        self.desc_label = ctk.CTkLabel(
            self.text_box, text=description, font=FONT_MD, anchor="w"
        )
        self.desc_label.pack(side="left")

        # Preview of the details (see build_preview): smaller font and a muted
        # colour so it is clearly secondary to the title. With no details it
        # stays empty and is not shown at all (no stray "…").
        self.preview_text = build_preview(self.notes)
        self.preview_lbl = ctk.CTkLabel(
            self.text_box, text=self.preview_text, font=FONT_SM,
            text_color=TEXT_SECONDARY, anchor="w"
        )
        if self.preview_text:
            self.preview_lbl.pack(side="left", fill="x", expand=True, padx=(PAD_SM, 0))

        # self.desc_label = ctk.CTkLabel(
            # self, text=description, font=FONT_MD, anchor="w"
        # )
        # self.desc_label.grid(row=0, column=2, sticky="ew", padx=(0, PAD_SM), pady=PAD_SM)   # was column 1

        # NEW: double-click the text to edit -- first of the two
        # required "trigger editing" methods.
        self.desc_label.bind("<Double-Button-1>", lambda e: self._open_edit())
        # NEW: the preview and the empty space around it behave like the title.
        self.preview_lbl.bind("<Double-Button-1>", lambda e: self._open_edit())
        self.text_box.bind("<Double-Button-1>", lambda e: self._open_edit())

        # -- "..." menu button ----------------------------------------------
        # NEW: second required trigger -- opens the same menu as
        # right-click, giving the user two equivalent ways in.
        # UPDATE (icons round): the "•••" button was replaced by three icon
        # buttons (copy / edit / delete). The right-click menu and the
        # double-click on the title still work as before. The old button code
        # is kept below as comments for reference.
        self.copy_btn = IconButton(self, "copy", command=self._copy)
        self.copy_btn.grid(row=0, column=3, padx=(PAD_XS, 0), pady=PAD_XS)

        self.edit_btn = IconButton(self, "pencil", command=self._open_edit)
        self.edit_btn.grid(row=0, column=4, padx=0, pady=PAD_XS)

        # The trash icon turns red on hover (with a soft red background).
        self.delete_btn = IconButton(
            self, "trash", command=self._delete,
            hover=DANGER, hover_bg=DANGER_SOFT
        )
        self.delete_btn.grid(row=0, column=5, padx=(0, PAD_SM), pady=PAD_XS)

        # self.menu_btn = ctk.CTkButton(
            # self, text="•••", width=MENU_BTN_WIDTH, height=MENU_BTN_HEIGHT,   # was 28 x 28
            # font=FONT_MENU_BTN,                                              # was 12 bold
            # fg_color=TRANSPARENT, text_color=ICON_MUTED,
            # hover_color=SURFACE_SELECTED, corner_radius=RADIUS_BTN,         # accent-tinted hover (was SURFACE_HOVER)
            # command=self._open_menu
        # )
        # # pady is PAD_XS (was PAD_SM): the button is 8 px taller now, so the
        # # smaller padding keeps every task row the same height as before.
        # self.menu_btn.grid(row=0, column=3, padx=(PAD_XS, PAD_SM), pady=PAD_XS)   # was column 2
        # _style_menu_button(self.menu_btn)    # NEW: dots turn accent-coloured on hover

        # NEW: right-click anywhere on the row opens the same menu
        self.bind("<Button-3>", self._open_menu)
        self.desc_label.bind("<Button-3>", self._open_menu)
        self.preview_lbl.bind("<Button-3>", self._open_menu)    # NEW: same for the preview
        self.text_box.bind("<Button-3>", self._open_menu)

        # NEW: simple hover feedback (immediate colour swap -- see
        # module docstring for why this isn't a smooth fade)
        for widget in (self, self.text_box, self.desc_label, self.preview_lbl):   # UPDATE: + the new widgets
            widget.bind("<Enter>", lambda e: self.configure(fg_color=SURFACE_HOVER))
            widget.bind("<Leave>", lambda e: self.configure(fg_color=SURFACE))

        self._apply_style(completed)

    # ----------------------------------------------------------
    # Visual state
    # ----------------------------------------------------------

    def _apply_style(self, completed: bool):
        """Grey-out + strike-through the label when completed."""
        if completed:
            self.desc_label.configure(
                text_color=COMPLETED_TASK_TEXT,
                font=(FONT_MD[0], FONT_MD[1], "overstrike")
            )
        else:
            self.desc_label.configure(text_color=TEXT_PRIMARY, font=FONT_MD)

    def update_status(self, completed: bool):
        self._apply_style(completed)

    # ----------------------------------------------------------
    # Actions
    # ----------------------------------------------------------

    def _on_dropped(self, cards):
        """
        NEW: called by the DragHandle after a drag that changed the order.
        `cards` is the new top-to-bottom list of TaskRows in this folder;
        MidFrame turns it into a list of task ids and saves it.
        """
        self.midframe.reorder_tasks(self.project_id, [c.task_id for c in cards])

    def _on_toggle(self):
        completed = self.check_var.get() == "on"
        self.midframe.toggle_task(self.project_id, self.task_id, completed)
        self._apply_style(completed)

    def _open_menu(self, event=None):
        """
        Build and show a small right-click-style menu with Edit
        and Delete. Used by BOTH the "..." button and an actual
        right-click, so both trigger methods stay in sync.
        """
        menu = _new_menu(self)    # UPDATE: larger font (was a plain tk.Menu(self, tearoff=0))
        menu.add_command(label="Edit task…", command=self._open_edit)
        menu.add_command(label="Delete task", command=self._delete)

        # Position at the mouse if triggered by right-click, else
        # just below the "..." button
        if event is not None:
            menu.tk_popup(event.x_root, event.y_root)
        else:
            # UPDATE: the "..." button no longer exists, so the pen icon is the anchor.
            x = self.edit_btn.winfo_rootx()
            y = self.edit_btn.winfo_rooty() + self.edit_btn.winfo_height()
            menu.tk_popup(x, y)

    def _open_edit(self):
        """Open the shared EditDialog pre-filled with title + notes."""
        EditDialog(
            self, dialog_title="Edit Task",
            initial_title=self.description,
            initial_notes=self.notes,
            on_save=lambda new_title, new_notes: self.midframe.edit_task(
                self.project_id, self.task_id, new_title, new_notes
            )
        )

    def _delete(self):
        self.midframe.delete_task(self.project_id, self.task_id)

    def _copy(self):
        """
        NEW: copy this task to the clipboard, then flash a check mark.

        Exact format (plain text):
            <title>
            <one blank line>
            <details>
        A task without details copies just the title (no trailing blank
        lines). Line breaks inside the details are kept as they are.
        """
        if self.notes.strip():
            text = f"{self.description}\n\n{self.notes}"
        else:
            text = self.description

        self.clipboard_clear()
        self.clipboard_append(text)

        # Confirmation without a dialog: the copy icon becomes a green check
        # for a moment and then changes back by itself.
        self.copy_btn.flash("check", SUCCESS)


# ==============================================================
# CommentRow  --  one numbered comment at the top of an open folder  (NEW, round 6)
# ==============================================================

class CommentRow(ctk.CTkFrame):
    """
    One comment:   "1.  <italic text>"   followed by copy / pen / trash icons.

    - The NUMBER is not stored and cannot be edited: FolderCard.refresh_comments
      gives every row its position in the list (1, 2, 3 ...). That is why
      deleting a comment renumbers the others, and why they cannot be moved.
    - The pen icon turns the text into an INLINE editor. Enter saves, Shift+Enter
      starts a new line, Esc cancels, the check-mark icon saves, and clicking
      somewhere else in the app saves too. (Saving an empty text never changes an
      existing comment, and a new empty comment is simply dropped.)
    - A brand-new comment (a "draft", comment_id is None) is NOT in the database
      until it has text, so the database never contains empty comments.
    - Copy puts ONLY the comment text on the clipboard (no number).
    """

    def __init__(self, master, midframe, project_id, comment_id, number, text):
        super().__init__(master, fg_color=SURFACE, corner_radius=RADIUS_CARD)

        self.midframe   = midframe            # back-reference for the database actions
        self.project_id = project_id
        self.comment_id = comment_id          # None while this is an unsaved draft
        self.number     = number              # 1, 2, 3 ... (just the position, never stored)
        self.text       = text
        self.is_draft   = comment_id is None

        self._editor    = None                # the inline text box while editing
        self._finishing = False               # guards against saving twice
        self._wrap      = 0

        self.grid_columnconfigure(1, weight=1)

        # -- number ("1.") -------------------------------------------------
        self.number_lbl = ctk.CTkLabel(
            self, text=f"{number}.", font=FONT_MD,
            text_color=TEXT_SECONDARY, width=30, anchor="e"
        )
        self.number_lbl.grid(row=0, column=0, padx=(PAD_SM, PAD_XS), pady=PAD_SM, sticky="ne")

        # -- the comment text: italic, in the colour COMMENT_TEXT from settings.py --
        self.text_lbl = ctk.CTkLabel(
            self, text=text, font=FONT_COMMENT, text_color=COMMENT_TEXT,
            anchor="w", justify="left"
        )
        self.text_lbl.grid(row=0, column=1, sticky="ew", padx=(0, PAD_SM), pady=PAD_SM)

        # -- icons: copy / edit / delete (the same icons the task rows use) --
        self.copy_btn = IconButton(self, "copy", command=self._copy)
        self.copy_btn.grid(row=0, column=2, padx=(PAD_XS, 0), pady=PAD_XS, sticky="n")

        self.edit_btn = IconButton(self, "pencil", command=self.start_edit)
        self.edit_btn.grid(row=0, column=3, padx=0, pady=PAD_XS, sticky="n")

        self.delete_btn = IconButton(
            self, "trash", command=self._delete, hover=DANGER, hover_bg=DANGER_SOFT
        )
        self.delete_btn.grid(row=0, column=4, padx=(0, PAD_SM), pady=PAD_XS, sticky="n")

        # Long comments wrap onto several lines instead of running off the window.
        self.bind("<Configure>", self._on_resize)

    # ----------------------------------------------------------
    # Layout
    # ----------------------------------------------------------

    def _on_resize(self, event):
        """Keep the text label's wrap width in step with the width of the row."""
        wrap = max(120, event.width - 200)        # 200 px = number + three icons + padding
        if abs(wrap - self._wrap) > 2:
            self._wrap = wrap
            self.text_lbl.configure(wraplength=wrap)

    # ----------------------------------------------------------
    # Inline editing
    # ----------------------------------------------------------

    def start_edit(self):
        """Replace the text by an editable box (also used for a new, empty comment)."""
        if self._editor is not None:
            self._editor.focus_set()
            return

        self.text_lbl.grid_remove()
        self._editor = ctk.CTkTextbox(
            self, height=76, wrap="word", font=FONT_COMMENT, text_color=COMMENT_TEXT,
            corner_radius=RADIUS_BTN, border_width=1, border_color=ACCENT
        )
        self._editor.grid(row=0, column=1, sticky="ew", padx=(0, PAD_SM), pady=PAD_SM)
        self._editor.insert("1.0", self.text)
        self._editor.focus_set()

        self._editor.bind("<Return>", self._on_return)
        self._editor.bind("<Escape>", lambda e: self._cancel_edit())
        # Leaving the box (a click elsewhere in the app) saves it.
        self._editor.bind("<FocusOut>", lambda e: self.after(30, self._check_blur))

        # While editing only one icon is shown: the check mark = save.
        self.copy_btn.grid_remove()
        self.delete_btn.grid_remove()
        self.edit_btn.set_icon("check")
        self.edit_btn.set_palette(idle=SUCCESS, hover=SUCCESS)
        self.edit_btn.configure(command=self._commit_edit)

    def _on_return(self, event):
        """Enter saves; Shift+Enter inserts a line break (the normal text-box behaviour)."""
        if event.state & 0x0001:          # the Shift key is held
            return None
        self._commit_edit()
        return "break"                    # stop the text box from adding a line break

    def _check_blur(self):
        """
        The editor lost the keyboard focus. Save only if the focus went to another
        part of THIS app. If it is gone altogether (the user switched to another
        program) keep editing, so a half-written comment is not dropped.
        """
        if self._editor is None or self._finishing:
            return
        try:
            focused = self.focus_get()
        except (KeyError, tk.TclError):
            focused = None
        if focused is None:
            return
        widget = focused
        while widget is not None:
            if widget is self._editor:
                return                    # still inside the editor
            widget = getattr(widget, "master", None)
        self._commit_edit()

    def _commit_edit(self):
        """Save the edited text (see the class docstring for the exact rules)."""
        if self._editor is None or self._finishing:
            return
        self._finishing = True
        new_text = self._editor.get("1.0", "end").strip()

        if self.is_draft:
            if new_text:
                self.midframe.add_comment(self.project_id, new_text)   # saves + redraws (this row is replaced)
            else:
                self.midframe.discard_comment_draft(self.project_id, self)
            return

        if new_text and new_text != self.text:
            self.midframe.edit_comment(self.project_id, self.comment_id, new_text)
        else:
            self._end_edit()              # empty or unchanged: keep the old text

    def _cancel_edit(self):
        """Esc: throw the change away."""
        if self._editor is None or self._finishing:
            return "break"
        if self.is_draft:
            self._finishing = True
            self.midframe.discard_comment_draft(self.project_id, self)
        else:
            self._end_edit()
        return "break"

    def _end_edit(self):
        """Back to the normal (read-only) look."""
        if self._editor is not None:
            self._editor.destroy()
            self._editor = None
        self._finishing = False
        self.text_lbl.grid()
        self.copy_btn.grid()
        self.delete_btn.grid()
        self.edit_btn.set_icon("pencil")
        self.edit_btn.set_palette(idle=ICON_IDLE, hover=ACCENT)
        self.edit_btn.configure(command=self.start_edit)

    # ----------------------------------------------------------
    # Other actions
    # ----------------------------------------------------------

    def _copy(self):
        """
        Copy ONLY the comment text (no number, no project title) to the clipboard,
        then flash a check mark -- the same confirmation the task copy uses.
        """
        self.clipboard_clear()
        self.clipboard_append(self.text)
        self.copy_btn.flash("check", SUCCESS)

    def _delete(self):
        self.midframe.delete_comment(self.project_id, self.comment_id)


# ==============================================================
# FolderCard  --  one collapsible folder (formerly ProjectCard)
# ==============================================================

class FolderCard(ctk.CTkFrame):
    """
    A collapsible folder:
      - Header row: expand/collapse arrow, name, task badge, "..."
      - Body (hidden until expanded): task list + inline add-task bar

    Renaming a folder and deleting it are triggered the same two
    ways as tasks: the "..." button or right-click on the header.

    UPDATE (drag-and-drop + deadlines): the header now also holds a "≡"
    DragHandle and a clickable Deadline cell. Header grid columns:
    0 arrow | 1 handle | 2 name (expands) | 3 deadline | 4 badge | 5 "..." menu.

    UPDATE (icons round): the "..." menu was replaced by icon buttons and the
    badge moved to the left of the deadline, so the columns are now:
    0 arrow | 1 handle | 2 name (expands) | 3 badge | 4 deadline | 5 (reserved
    for the bell) | 6 calendar icon | 7 pen icon | 8 trash icon.
    The header background is also coloured by task completion (apply_status).

    UPDATE (batch 2): column 5 now holds the bell icon (mute / un-mute
    reminders). While a task is being typed the calendar / pen / trash icons
    are locked (see set_locked).
    """

    def __init__(self, master, midframe, project_id, title, deadline=None, muted=False):
        super().__init__(
            master, fg_color=SURFACE, corner_radius=RADIUS_LG,
            border_width=1, border_color=BORDER_SUBTLE
        )
        self.midframe   = midframe
        self.project_id = project_id
        self.title_text = title
        self.expanded   = False
        self.deadline   = deadline   # NEW: ISO "YYYY-MM-DD" text or None (no deadline)

        # NEW (status colours): which colour set the header uses right now, and
        # whether the pointer is over it. Starts neutral; refresh_badge() below
        # switches it as soon as the real task counts are known.
        self._status  = "empty"
        self._palette = STATUS_PALETTES["empty"]
        self._hovered = False

        # NEW (batch 2): bell state + "adding a task" lock state (runtime only).
        self.muted = bool(muted)         # True = no launch reminders for this folder (saved in SQLite)
        self._locked = False             # True while the project-level icons are greyed out
        self._task_mode = False          # True while THIS folder's task entry has focus + text
        self._entry_focused = False      # does the task entry have keyboard focus right now?

        self.grid_columnconfigure(0, weight=1)

        self._build_header(title)
        self._build_body()
        self.refresh_badge()
        self.refresh_deadline()      # NEW: fill the Deadline cell (date + days left)

    # ----------------------------------------------------------
    # Header (always visible)
    # ----------------------------------------------------------

    def _build_header(self, title: str):
        # UPDATE (status colours): the header is now a real coloured band (it used
        # to be transparent). Its colour is set by apply_status(); the small
        # padding keeps the band's rounded corners inside the card's border.
        self.header = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=RADIUS_LG - 4)
        self.header.grid(row=0, column=0, sticky="ew", padx=PAD_XS, pady=PAD_XS)
        self.header.grid_columnconfigure(1, weight=1)
        # UPDATE: the name moved to column 2 (handle took column 1), so that is
        # now the column that stretches; column 1 must stay fixed-width.
        self.header.grid_columnconfigure(2, weight=1)
        self.header.grid_columnconfigure(1, weight=0)

        # -- Expand/collapse arrow --
        self.toggle_btn = ctk.CTkButton(
            self.header, text="▸", width=28, height=28,
            font=(FONT_MD[0], 13, "bold"),
            fg_color=TRANSPARENT, text_color=ICON_MUTED,
            hover_color=SURFACE_HOVER, corner_radius=RADIUS_BTN,
            command=self.toggle_expand
        )
        self.toggle_btn.grid(row=0, column=0, padx=(PAD_SM, PAD_XS), pady=PAD_SM)

        # -- Drag handle (NEW) --
        # Sits right next to the folder name. Dragging it re-orders this
        # folder among all folders; _on_dropped (below) saves the result.
        self.drag_handle = DragHandle(self.header, card=self, on_drop=self._on_dropped)
        self.drag_handle.grid(row=0, column=1, padx=(0, PAD_XS), pady=PAD_SM)

        # -- Folder name --
        self.title_lbl = ctk.CTkLabel(
            self.header, text=title, font=FONT_LG,
            text_color=TEXT_PRIMARY, anchor="w"
        )
        self.title_lbl.grid(row=0, column=2, sticky="ew", pady=PAD_SM)   # was column 1

        # NEW: double-click the folder name to rename it -- same
        # editing pattern used for tasks, for consistency.
        self.title_lbl.bind("<Double-Button-1>", lambda e: self._open_rename())

        # -- Task-count badge, e.g. "2 / 5" --
        self.badge_lbl = ctk.CTkLabel(
            self.header, text="—", font=FONT_SM,
            text_color=TEXT_SECONDARY, width=44
        )
        self.badge_lbl.grid(row=0, column=3, padx=PAD_XS, pady=PAD_SM)   # was column 2 (later 4; now 3, left of the deadline)

        # -- Deadline cell (NEW) --
        # Two lines: the date, and below it "N days left" / "Due today" /
        # "N days overdue". Clicking it opens the calendar to set, change or
        # clear the deadline. It is NOT in the click-to-expand binding loop
        # further down, so clicking it never toggles the folder.
        #
        # UPDATE (polish round): the cell is now ONE ROW with TWO COLUMNS side
        # by side instead of two stacked lines, in a larger font:
        #       2026-12-01  |  18 days left
        # A small frame (deadline_box) holds three labels: the date (right-
        # aligned), a thin "|" divider and the days-left text (left-aligned).
        # Fixed label widths make the "|" line up from one folder to the next.
        # The old single label (deadline_lbl) was replaced by these widgets.
        self.deadline_box = ctk.CTkFrame(self.header, fg_color="transparent", cursor="hand2")
        self.deadline_box.grid(row=0, column=4, padx=PAD_XS, pady=PAD_SM)   # UPDATE: was column 3

        self.deadline_date_lbl = ctk.CTkLabel(
            self.deadline_box, text="—", font=FONT_DEADLINE_BOLD,
            text_color=TEXT_SECONDARY, width=96, anchor="e", cursor="hand2"
        )
        self.deadline_date_lbl.grid(row=0, column=0)

        self.deadline_sep_lbl = ctk.CTkLabel(
            self.deadline_box, text="", font=FONT_DEADLINE,
            text_color=ICON_MUTED, width=16, cursor="hand2"
        )
        self.deadline_sep_lbl.grid(row=0, column=1)

        self.deadline_days_lbl = ctk.CTkLabel(
            self.deadline_box, text="", font=FONT_DEADLINE,
            text_color=TEXT_SECONDARY, width=122, anchor="w", cursor="hand2"
        )
        self.deadline_days_lbl.grid(row=0, column=2)

        # Clicking ANY part of the cell opens the calendar. Each widget needs
        # its own binding because a click on a child label is not passed to
        # the frame around it.
        for part in (self.deadline_box, self.deadline_date_lbl,
                     self.deadline_sep_lbl, self.deadline_days_lbl):
            part.bind("<Button-1>", lambda e: self._open_deadline_picker())

        # -- "..." menu button --
        # UPDATE (icons round): the "•••" button was replaced by three icons:
        # calendar = edit deadline, pen = rename, trash = delete. (Column 5 is
        # reserved for the bell icon.) Right-click on the header still opens
        # the old menu. The old button code is kept below as comments.
        # UPDATE (bell): the bell sits in the reserved column 5, right next to
        # the deadline. Click it to mute / un-mute THIS folder's deadline
        # reminders; the bell with a slash means "muted". Saved in SQLite.
        self.bell_btn = IconButton(
            self.header, "bell-off" if self.muted else "bell", command=self._toggle_mute
        )
        self.bell_btn.grid(row=0, column=5, padx=(PAD_XS, 0), pady=PAD_XS)

        self.edit_deadline_btn = IconButton(
            self.header, "calendar", command=self._open_deadline_picker
        )
        self.edit_deadline_btn.grid(row=0, column=6, padx=(PAD_XS, 0), pady=PAD_XS)

        self.rename_btn = IconButton(self.header, "pencil", command=self._open_rename)
        self.rename_btn.grid(row=0, column=7, padx=0, pady=PAD_XS)

        self.delete_btn = IconButton(self.header, "trash", command=self._delete)
        self.delete_btn.grid(row=0, column=8, padx=(0, PAD_SM), pady=PAD_XS)

        # self.menu_btn = ctk.CTkButton(
            # self.header, text="•••", width=MENU_BTN_WIDTH, height=MENU_BTN_HEIGHT,   # was 28 x 28
            # font=FONT_MENU_BTN,                                                   # was 12 bold
            # fg_color=TRANSPARENT, text_color=ICON_MUTED,
            # hover_color=SURFACE_SELECTED, corner_radius=RADIUS_BTN,              # accent-tinted hover (was SURFACE_HOVER)
            # command=self._open_menu
        # )
        # # pady is PAD_XS (was PAD_SM) so the taller button does not make the
        # # folder header taller than it was.
        # self.menu_btn.grid(row=0, column=5, padx=(PAD_XS, PAD_SM), pady=PAD_XS)   # was column 3
        # _style_menu_button(self.menu_btn)    # NEW: dots turn accent-coloured on hover

        # Clicking anywhere else on the header row also toggles
        # expand/collapse -- feels like a normal accordion.
        for widget in (self.header, self.title_lbl):
            widget.bind("<Button-1>", lambda e: self.toggle_expand())
            widget.bind("<Button-3>", self._open_menu)
            # UPDATE (status colours): hover now uses the header's own colour set
            # (see _set_hover / _on_header_leave) instead of one fixed grey.
            widget.bind("<Enter>", lambda e: self._set_hover(True))
            widget.bind("<Leave>", lambda e: self._on_header_leave())

    # ----------------------------------------------------------
    # Body (tasks + inline add-task bar) -- created hidden
    # ----------------------------------------------------------

    def _build_body(self):
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.grid(row=1, column=0, sticky="ew", padx=PAD_SM, pady=(0, PAD_SM))
        self.body.grid_columnconfigure(0, weight=1)
        self.body.grid_remove()   # Start collapsed -- this is the "folder" behaviour

        # NEW (round 6): the COMMENT SECTION. It is the very first thing in the open
        # folder (row 0), above the add bar and the task list. It is hidden with
        # grid_remove() while the folder has no comments, so a folder without
        # comments shows nothing here at all (no placeholder, no empty space).
        self.comments_container = ctk.CTkFrame(self.body, fg_color="transparent")
        self.comments_container.grid(row=0, column=0, sticky="ew")
        self.comments_container.grid_columnconfigure(0, weight=1)
        self.comments_container.grid_remove()

        # Container that holds the TaskRow widgets. Kept separate
        # from the add-task bar so refresh_tasks() can clear just
        # this part without rebuilding the entry field below.
        self.tasks_container = ctk.CTkFrame(self.body, fg_color="transparent")
        # UPDATE (batch 2): the add-task bar is now ABOVE the list, so the list
        # moved to row 1 (the comment above says "below"; it now reads "above").
        self.tasks_container.grid(row=2, column=0, sticky="ew")   # was row 0 (row 1 in batch 2; row 2 since round 6: the comments take row 0)
        self.tasks_container.grid_columnconfigure(0, weight=1)

        # -- Inline "add task" bar, local to this folder --
        add_bar = ctk.CTkFrame(self.body, fg_color="transparent")
        add_bar.grid(row=1, column=0, sticky="ew", pady=(0, PAD_XS))   # was row 1, pady=(PAD_XS, 0): now at the TOP (round 6: row 1, right below the comments)
        add_bar.grid_columnconfigure(0, weight=1)

        self.task_entry = ctk.CTkEntry(
            add_bar, placeholder_text="New task…", height=32,
            font=FONT_MD, corner_radius=RADIUS_BTN, border_color=ACCENT
        )
        self.task_entry.grid(row=0, column=0, sticky="ew", padx=(0, PAD_SM))
        self.task_entry.bind("<Return>", lambda e: self._add_task())

        # NEW (batch 2, "adding a task" lock): keep track of focus and of whether
        # there is a draft, so the project-level controls can be greyed out.
        self.task_entry.bind("<FocusIn>", lambda e: self._on_entry_focus(True))
        self.task_entry.bind("<FocusOut>", lambda e: self._on_entry_focus(False))
        self.task_entry.bind("<KeyRelease>", lambda e: self._update_task_mode())
        # Cut / paste with the mouse or the menu do not produce key events, so
        # they are checked once the text has actually changed.
        self.task_entry.bind("<<Paste>>", lambda e: self.after_idle(self._update_task_mode))
        self.task_entry.bind("<<Cut>>", lambda e: self.after_idle(self._update_task_mode))
        self.task_entry.bind("<Escape>", lambda e: self._cancel_task())

        # UPDATE (round 6): the single "Add" button is now "Add Task", and a second
        # button "Add Comment" sits next to it. "Add Task" uses the text typed in the
        # box; "Add Comment" does not use the box: it opens a NEW EMPTY COMMENT at
        # the end of the comment list, ready to be typed into (see _add_comment).
        self.add_task_btn = ctk.CTkButton(
            add_bar, text="Add Task", width=84, height=32, font=FONT_MD,
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            corner_radius=RADIUS_BTN, command=self._add_task
        )
        self.add_task_btn.grid(row=0, column=1)

        # Outlined (secondary) look, the same as the "Deadline" button of the
        # "New folder" bar, so it reads as the lesser action.
        self.add_comment_btn = ctk.CTkButton(
            add_bar, text="Add Comment", width=112, height=32, font=FONT_MD,
            fg_color=TRANSPARENT, border_width=1, border_color=BORDER_SUBTLE,
            text_color=TEXT_PRIMARY, hover_color=SURFACE_HOVER,
            corner_radius=RADIUS_BTN, command=self._add_comment
        )
        self.add_comment_btn.grid(row=0, column=2, padx=(PAD_SM, 0))

    # ----------------------------------------------------------
    # Expand / collapse
    # ----------------------------------------------------------

    def toggle_expand(self):
        self.set_expanded(not self.expanded)

    def set_expanded(self, expanded: bool):
        self.expanded = expanded
        if expanded:
            self.body.grid()
            self.toggle_btn.configure(text="▾")
            self.refresh_comments()     # NEW (round 6): comments only matter while the folder is open
            self.refresh_tasks()
        else:
            self.body.grid_remove()
            self.toggle_btn.configure(text="▸")
        # NEW: an expanded folder keeps the lighter "selected" shade of its colour.
        self._paint_header()

    # ----------------------------------------------------------
    # Data refresh
    # ----------------------------------------------------------

    def refresh_tasks(self):
        """Reload this folder's tasks from the DB and redraw rows."""
        for widget in self.tasks_container.winfo_children():
            widget.destroy()

        tasks = self.midframe.db.get_tasks(self.project_id)

        if not tasks:
            ctk.CTkLabel(
                self.tasks_container, text="No tasks yet — add one below.",
                font=FONT_SM, text_color=TEXT_SECONDARY
            ).pack(pady=PAD_SM)
            return

        for task_id, description, notes, completed in tasks:
            row = TaskRow(
                self.tasks_container, self.midframe, self.project_id,
                task_id, description, notes, bool(completed)
            )
            row.pack(fill="x", pady=(0, PAD_XS))

    def refresh_comments(self):
        """
        NEW (round 6): reload this folder's comments from the DB and redraw them.

        The numbers are handed out here, by position (1, 2, 3 ...) -- they are
        never stored. So after a comment was deleted this simply numbers the
        remaining ones again.
        """
        for widget in self.comments_container.winfo_children():
            widget.destroy()

        comments = self.midframe.db.get_comments(self.project_id)
        for number, (comment_id, text) in enumerate(comments, start=1):
            CommentRow(
                self.comments_container, self.midframe, self.project_id,
                comment_id, number, text
            ).pack(fill="x", pady=(0, PAD_XS))

        self._update_comments_visibility()

    def _update_comments_visibility(self):
        """Show the comment section only if it has something in it (nothing otherwise)."""
        if self.comments_container.winfo_children():
            self.comments_container.grid()
        else:
            self.comments_container.grid_remove()

    def _add_comment(self):
        """
        "Add Comment": open a new, empty comment at the END of the list, ready for
        typing. It is saved once it has text (see CommentRow). Only one new
        comment can be open at a time.
        """
        # A comment that is being edited is saved first, so no text is lost.
        for row in self.comments_container.winfo_children():
            if isinstance(row, CommentRow) and row._editor is not None and not row.is_draft:
                row._commit_edit()

        rows = [w for w in self.comments_container.winfo_children() if isinstance(w, CommentRow)]
        for row in rows:
            if row.is_draft:
                row.start_edit()
                return

        draft = CommentRow(
            self.comments_container, self.midframe, self.project_id,
            None, len(rows) + 1, ""
        )
        draft.pack(fill="x", pady=(0, PAD_XS))
        self._update_comments_visibility()
        draft.start_edit()

    def refresh_badge(self):
        """Update the "done / total" badge from the DB."""
        total, done = self.midframe.db.get_project_task_counts(self.project_id)
        self.badge_lbl.configure(text=f"{done} / {total}" if total > 0 else "—")
        # NEW: the same two numbers decide the header colour.
        self.apply_status(total, done)

    def apply_status(self, total: int, done: int):
        """
        NEW: colour the header by task completion and re-tint everything on it.

        Green = all tasks done, orange = some done, red = none done, neutral =
        no tasks (see completion_status). Text and icon colours are switched
        together with the background so they always stay readable.
        Called from refresh_badge(), i.e. after every add / toggle / delete.
        """
        status = completion_status(total, done)
        palette = STATUS_PALETTES[status]
        self._status = status
        self._palette = palette

        self.title_lbl.configure(text_color=palette["text"])
        self.badge_lbl.configure(text_color=palette["muted"])
        self.deadline_sep_lbl.configure(text_color=palette["muted"])
        self.drag_handle.configure(text_color=palette["glyph"])

        # Hovered icon buttons get a background a little lighter than the band.
        icon_bg = self._lift(palette["hover"])
        self.toggle_btn.configure(text_color=palette["glyph"], hover_color=icon_bg)
        for button in (self.edit_deadline_btn, self.rename_btn):
            button.set_palette(idle=palette["icon"], hover=palette["icon_hover"], hover_bg=icon_bg)
        self.delete_btn.set_palette(idle=palette["icon"], hover=palette["trash_hover"], hover_bg=icon_bg)
        self._icon_bg = icon_bg          # remembered so the bell can be re-tinted later
        self._apply_bell_palette()       # NEW (batch 2): the bell follows the header colour too

        self._paint_header()
        self.refresh_deadline()      # its colours come from the palette too

    def _paint_header(self):
        """Fill the header with the base colour, or the lighter variant while hovered/expanded."""
        palette = self._palette
        lighter = self._hovered or self.expanded
        self.header.configure(fg_color=palette["hover"] if lighter else palette["bg"])

    def _set_hover(self, hovered: bool):
        self._hovered = hovered
        self._paint_header()

    def _on_header_leave(self):
        """Only drop the hover colour when the pointer REALLY left the header."""
        if not _pointer_inside(self.header):
            self._set_hover(False)

    def _lift(self, colour_pair, amount: float = 0.18):
        """Return a (light, dark) colour pair mixed `amount` of the way towards white."""
        lifted = []
        for colour in colour_pair:
            red, green, blue = (v // 257 for v in self.winfo_rgb(colour))   # Tk colour -> 0..255
            lifted.append("#%02x%02x%02x" % (
                int(red + (255 - red) * amount),
                int(green + (255 - green) * amount),
                int(blue + (255 - blue) * amount)))
        return tuple(lifted)

    def refresh_deadline(self):
        """
        NEW: redraw the Deadline cell from self.deadline. Called when the
        card is built, after the deadline is edited, and when midnight passes
        (so "days left" never goes stale). Overdue deadlines use the red
        DANGER colour; everything else stays muted.
        """
        date_line, days_line, overdue = describe_deadline(self.deadline)
        # UPDATE (polish round): the two values now go into two side-by-side
        # labels. Overdue turns BOTH red (as before); otherwise the date is
        # the prominent bold primary colour and "days left" stays muted.
        # With no deadline only the dash is shown and the divider is hidden.
        # UPDATE (status colours): the colours now come from the header's colour
        # set so they stay readable on the green / orange / red backgrounds.
        # On the neutral header the set holds the same colours as before.
        p = self._palette
        self.deadline_date_lbl.configure(
            text=date_line,
            text_color=p["overdue"] if overdue else (p["text"] if days_line else p["muted"])
        )
        self.deadline_sep_lbl.configure(text="|" if days_line else "")
        self.deadline_days_lbl.configure(
            text=days_line,
            text_color=p["overdue"] if overdue else p["muted"]
        )

    def set_deadline(self, iso_text):
        """NEW: store the new deadline on the card and redraw the cell."""
        self.deadline = iso_text
        self.refresh_deadline()

    def rename(self, new_title: str):
        """Called by MidFrame after a successful DB rename."""
        self.title_text = new_title
        self.title_lbl.configure(text=new_title)

    # ----------------------------------------------------------
    # Actions
    # ----------------------------------------------------------

    def _add_task(self):
        description = self.task_entry.get().strip()
        if not description:
            messagebox.showwarning("Warning", "Please enter a task description.")
            return
        self.midframe.add_task(self.project_id, description)
        self.task_entry.delete(0, "end")
        self.task_entry.focus_set()
        self._update_task_mode()    # NEW: the draft is gone, so the lock is released

    # ----------------------------------------------------------
    # Bell (mute) + "adding a task" lock  (NEW -- round 4, batch 2)
    # ----------------------------------------------------------

    def _apply_bell_palette(self):
        """A normal bell is bright; the muted bell-with-slash is dimmer."""
        palette = self._palette
        idle = palette["icon_dim"] if self.muted else palette["icon"]
        self.bell_btn.set_palette(idle=idle, hover=palette["icon_hover"], hover_bg=self._icon_bg)

    def set_muted(self, muted: bool):
        """Called by MidFrame after the new mute state was saved: swap the icon."""
        self.muted = bool(muted)
        self.bell_btn.set_icon("bell-off" if self.muted else "bell")
        self._apply_bell_palette()

    def _toggle_mute(self):
        """Bell clicked: ask MidFrame to save the opposite state."""
        self.midframe.set_folder_muted(self.project_id, not self.muted)

    def set_locked(self, locked: bool):
        """
        Grey out (or restore) the project-level icons: calendar, pen, trash.
        The bell is NOT locked -- muting cannot lose any data. The right-click
        menu and the double-click rename are blocked by checks in the handlers.
        """
        self._locked = locked
        for button in (self.edit_deadline_btn, self.rename_btn, self.delete_btn):
            button.set_locked(locked)

    def _on_entry_focus(self, focused: bool):
        self._entry_focused = focused
        self._update_task_mode()

    def _update_task_mode(self):
        """
        Decide whether this folder is in "adding a task" mode and tell MidFrame
        when that changes. The mode is ON only while the task entry has
        keyboard focus AND already contains text (a draft is in progress):
        it ends when focus leaves, the box is emptied, Esc is pressed or the
        task is submitted. Clicking into an EMPTY box locks nothing.
        """
        active = self._entry_focused and bool(self.task_entry.get().strip())
        if active != self._task_mode:
            self._task_mode = active
            self.midframe.set_task_mode(self.project_id, active)

    def _cancel_task(self):
        """Esc in the task entry: throw the draft away and leave the box."""
        self.task_entry.delete(0, "end")
        self._entry_focused = False
        self.winfo_toplevel().focus_set()       # moves the keyboard focus away from the entry
        self._update_task_mode()
        return "break"

    def _on_dropped(self, cards):
        """
        NEW: called by the DragHandle after a drag that changed the order.
        `cards` is the new top-to-bottom list of FolderCards; MidFrame turns
        it into a list of project ids and saves it.
        """
        self.midframe.reorder_folders([c.project_id for c in cards])

    def _open_deadline_picker(self):
        """
        NEW: open the calendar popup just below the Deadline cell, pre-set to
        the current deadline (if any). The popup reports the choice through
        on_select: a date, or None when the user pressed "Clear".
        """
        if self._locked:             # NEW (batch 2): a task is being typed -> do nothing
            return
        CalendarPopup(
            self.winfo_toplevel(),
            initial=parse_deadline(self.deadline),
            on_select=lambda chosen: self.midframe.set_folder_deadline(
                self.project_id, chosen
            ),
            anchor=self.deadline_box    # UPDATE: was self.deadline_lbl (replaced by the two-column cell)
        )

    def _open_menu(self, event=None):
        """Same pattern as TaskRow._open_menu -- "..." and right-click share this."""
        if self._locked:             # NEW (batch 2): a task is being typed -> no menu
            return
        menu = _new_menu(self)    # UPDATE: larger font (was a plain tk.Menu(self, tearoff=0))
        menu.add_command(label="Rename folder…", command=self._open_rename)
        menu.add_command(label="Edit deadline…", command=self._open_deadline_picker)   # NEW
        menu.add_command(label="Delete folder", command=self._delete)

        if event is not None:
            menu.tk_popup(event.x_root, event.y_root)
        else:
            # UPDATE: the "..." button no longer exists, so the pen icon is the anchor.
            x = self.rename_btn.winfo_rootx()
            y = self.rename_btn.winfo_rooty() + self.rename_btn.winfo_height()
            menu.tk_popup(x, y)

    def _open_rename(self):
        if self._locked:             # NEW (batch 2): a task is being typed -> do nothing
            return
        EditDialog(
            self, dialog_title="Rename Folder",
            initial_title=self.title_text,
            initial_notes=None,   # None => folder mode, no details box
            on_save=lambda new_title, _: self.midframe.rename_folder(
                self.project_id, new_title
            )
        )

    def _delete(self):
        if self._locked:             # NEW (batch 2): a task is being typed -> do nothing
            return
        self.midframe.delete_folder(self.project_id)


# ==============================================================
# MidFrame  --  the main content area (now a single-column accordion)
# ==============================================================

class MidFrame(ctk.CTkFrame):
    """
    Holds a scrollable list of FolderCard widgets. Replaces the old
    two-column project/task layout -- see module docstring for why.
    """

    def __init__(self, master, controller=None):
        super().__init__(master, fg_color="transparent")

        # Same DB-sharing pattern as before: use the controller's
        # shared DatabaseManager, never create a second one here.
        self.controller = controller
        self.db = controller.db if controller else DatabaseManager()

        self.folder_cards = {}   # project_id -> FolderCard

        # NEW (batch 2): ids of the folders whose task entry is in "adding a
        # task" mode right now. Non-empty = the project-level controls are locked.
        self._task_mode_ids = set()

        # NEW (batch 2): a click that ends the mode must not "fall through" to the
        # control that was greyed out when the click started. See set_task_mode.
        self._mouse_down = False         # is mouse button 1 held down right now?
        self._unlock_pending = False     # unlock requested while the button was held down

        # NEW: used by _check_new_day() to notice when midnight has passed.
        self._last_seen_day = date.today()
        self._day_check_job = None

        # MidFrame still occupies row 1 of the root window's grid,
        # configured in main.py -- unchanged from before.
        # UPDATE (round 4): extra space on top now that the title bar row is gone.
        self.grid(row=1, column=0, sticky="nsew", padx=PAD_LG, pady=(PAD_LG, PAD_SM))
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Single scrollable column now holds every folder.
        self.folders_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.folders_scroll.grid(row=0, column=0, sticky="nsew")
        self.folders_scroll.grid_columnconfigure(0, weight=1)

        self.load_folders()

        # NEW: start the once-a-minute "has the date changed?" check.
        self._day_check_job = self.after(60_000, self._check_new_day)

        # NEW (batch 2): window-wide mouse handlers for the "adding a task" lock.
        # - press:   remembers that the button is down and, because plain tkinter
        #            does not move the keyboard focus when you click an empty part
        #            of the window, releases the focus from the task entry.
        # - release: finishes an unlock that had to wait for the button to come up.
        # add="+" keeps every other click binding working.
        self.winfo_toplevel().bind("<ButtonPress-1>", self._on_mouse_press, add="+")
        self.winfo_toplevel().bind("<ButtonRelease-1>", self._on_mouse_release, add="+")

    # ----------------------------------------------------------
    # Observer callback -- called by AppController (unchanged hook)
    # ----------------------------------------------------------

    def on_project_added(self, project_id: int):
        """Refresh the list and auto-expand the newly created folder."""
        self.load_folders()
        if project_id in self.folder_cards:
            self.folder_cards[project_id].set_expanded(True)

    # Kept for backward compatibility -- AppController falls back to
    # this name if on_project_added is ever unavailable.
    def load_projects(self):
        self.load_folders()

    # ----------------------------------------------------------
    # Folder list management
    # ----------------------------------------------------------

    def load_folders(self):
        """Fetch all folders (projects) and rebuild the accordion list."""
        for widget in self.folders_scroll.winfo_children():
            widget.destroy()
        self.folder_cards = {}

        # NEW (batch 2): the old cards are gone, so no folder can still be in
        # "adding a task" mode; the new cards start unlocked.
        if self._task_mode_ids:
            self._task_mode_ids.clear()
            self._unlock_pending = False
            self._notify_lock(False)

        projects = self.db.get_all_projects()

        if not projects:
            ctk.CTkLabel(
                self.folders_scroll, text="No folders yet.\nAdd one below ↓",
                font=FONT_SM, text_color=TEXT_SECONDARY, justify="center"
            ).pack(pady=PAD_LG)
            return

        # UPDATE: get_all_projects() now returns (id, title, deadline).
        # UPDATE (batch 2): get_all_projects() now returns (id, title, deadline, muted).
        for project_id, title, deadline, muted in projects:
            card = FolderCard(self.folders_scroll, self, project_id, title, deadline, bool(muted))
            card.pack(fill="x", pady=(0, PAD_SM))
            self.folder_cards[project_id] = card

    def rename_folder(self, project_id: int, new_title: str):
        try:
            if self.db.update_project_title(project_id, new_title):
                self.folder_cards[project_id].rename(new_title)
        except ValueError as e:
            # Raised when the new name collides with an existing folder
            messagebox.showerror("Duplicate name", str(e))

    def delete_folder(self, project_id: int):
        if not messagebox.askyesno(
            "Delete folder",
            "Delete this folder and all its tasks?\nThis cannot be undone.",
            icon="warning"
        ):
            return

        if self.db.delete_project(project_id):
            self.load_folders()
        else:
            messagebox.showerror("Error", "Failed to delete folder.")

    # ----------------------------------------------------------
    # Task management (delegated to by FolderCard / TaskRow)
    # ----------------------------------------------------------

    def add_task(self, project_id: int, description: str):
        try:
            self.db.add_task(project_id, description)
            self._refresh_folder(project_id)
        except Exception as e:
            logger.error(f"Error adding task: {e}")
            messagebox.showerror("Error", "Failed to add task.")

    def toggle_task(self, project_id: int, task_id: int, completed: bool):
        if self.db.update_task_status(task_id, completed):
            if project_id in self.folder_cards:
                self.folder_cards[project_id].refresh_badge()
        else:
            messagebox.showerror("Error", "Failed to update task.")

    def edit_task(self, project_id: int, task_id: int, new_description: str, new_notes: str):
        if self.db.update_task(task_id, new_description, new_notes):
            self._refresh_folder(project_id)
        else:
            messagebox.showerror("Error", "Failed to update task.")

    def delete_task(self, project_id: int, task_id: int):
        if not messagebox.askyesno("Delete task", "Delete this task?", icon="warning"):
            return

        if self.db.delete_task(task_id):
            self._refresh_folder(project_id)
        else:
            messagebox.showerror("Error", "Failed to delete task.")

    # ----------------------------------------------------------
    # Ordering + deadlines (NEW) -- called by DragHandle / FolderCard
    # ----------------------------------------------------------

    def reorder_folders(self, ordered_ids):
        """
        Save the folder order produced by a drag. The screen already shows
        the new order, so nothing is redrawn on success. If saving fails,
        the list is rebuilt from the database so what you SEE always matches
        what is SAVED.
        """
        if not self.db.reorder_projects(ordered_ids):
            messagebox.showerror("Error", "Failed to save the new folder order.")
            self.load_folders()

    def reorder_tasks(self, project_id: int, ordered_ids):
        """Same as reorder_folders, but for the tasks of ONE folder."""
        if not self.db.reorder_tasks(project_id, ordered_ids):
            messagebox.showerror("Error", "Failed to save the new task order.")
            self._refresh_folder(project_id)

    def set_folder_deadline(self, project_id: int, chosen):
        """
        Save a deadline picked in the calendar. `chosen` is a date, or None
        to remove the deadline. It is stored as ISO text ("2026-12-31").
        """
        iso_text = chosen.isoformat() if chosen else None
        if self.db.update_project_deadline(project_id, iso_text):
            if project_id in self.folder_cards:
                self.folder_cards[project_id].set_deadline(iso_text)
        else:
            messagebox.showerror("Error", "Failed to save the deadline.")

    # ----------------------------------------------------------
    # Bell, reminders and the "adding a task" lock (NEW -- batch 2)
    # ----------------------------------------------------------

    def set_folder_muted(self, project_id: int, muted: bool):
        """Save a bell click (mute / un-mute) and update the icon."""
        if self.db.set_project_muted(project_id, muted):
            if project_id in self.folder_cards:
                self.folder_cards[project_id].set_muted(muted)
        else:
            messagebox.showerror("Error", "Failed to save the reminder setting.")

    def show_deadline_alerts(self):
        """
        Called once per app start (see main.py). Shows ONE dialog that lists every
        un-muted folder due within 7 days or overdue, most urgent first. Shows
        nothing at all when no folder needs a reminder.
        """
        alerts = collect_deadline_alerts(self.db.get_all_projects())
        if not alerts:
            return
        title, message, level = format_deadline_alerts(alerts)
        parent = self.winfo_toplevel()
        if level == "error":
            messagebox.showerror(title, message, parent=parent)
        else:
            messagebox.showwarning(title, message, parent=parent)

    def set_task_mode(self, project_id: int, active: bool):
        """
        A folder's task entry entered / left "adding a task" mode. The
        controls are locked while ANY folder is in that mode.
        """
        was_locked = bool(self._task_mode_ids)
        if active:
            self._task_mode_ids.add(project_id)
        else:
            self._task_mode_ids.discard(project_id)
        is_locked = bool(self._task_mode_ids)
        if is_locked != was_locked:
            if not is_locked and self._mouse_down:
                # IMPORTANT: the mode ended because the user PRESSED the mouse on
                # something (CustomTkinter moves the focus to whatever is clicked).
                # CustomTkinter buttons run their command when the button is
                # RELEASED, so un-greying now would let that same click go
                # through to the greyed-out button (for example "Add Folder").
                # So the unlock waits until the mouse button is up again
                # (see _on_mouse_release); the greyed button stays dead until then.
                self._unlock_pending = True
            else:
                self._unlock_pending = False
                self._apply_lock(is_locked)

    def _apply_lock(self, locked: bool):
        """Grey out / restore the folder icons here and the Add Folder bar elsewhere."""
        for card in self.folder_cards.values():
            card.set_locked(locked)
        self._notify_lock(locked)

    def _notify_lock(self, locked: bool):
        """Tell the other frames (BottomFrame) through the AppController."""
        if self.controller is not None and hasattr(self.controller, "notify_task_mode"):
            self.controller.notify_task_mode(locked)

    def _on_mouse_press(self, event):
        """
        Mouse button 1 went down somewhere in the window.

        While the "adding a task" lock is on:
        - a click inside any text entry is left alone (Tk handles the focus);
        - any other click (empty space, a greyed-out button, a scrollbar...)
          moves the focus away from the task entry, which ends the mode. A
          greyed-out control does NOTHING with that click (it is still
          disabled while the button is down) and is re-enabled right after
          the button is released, so a second, deliberate click works.
        """
        self._mouse_down = True
        if not self._task_mode_ids:
            return
        widget = event.widget
        while widget is not None:
            if isinstance(widget, ctk.CTkEntry):
                return
            widget = getattr(widget, "master", None)
        self.winfo_toplevel().focus_set()

    def _on_mouse_release(self, event):
        """
        Mouse button 1 came up. The button's own release handler has already run
        (and ignored the click, because the button was still greyed out), so it
        is now safe to finish an unlock that was waiting for this moment.
        """
        self._mouse_down = False
        if self._unlock_pending:
            self._unlock_pending = False
            if not self._task_mode_ids:          # still no draft in progress
                self._apply_lock(False)

    def _check_new_day(self):
        """
        Runs once a minute. When the calendar date has changed since the last
        check (the app was left open overnight) every "days left" text is
        refreshed. Only the small deadline cells are redrawn, so expanded
        folders stay expanded.
        """
        today = date.today()
        if today != self._last_seen_day:
            self._last_seen_day = today
            for card in self.folder_cards.values():
                card.refresh_deadline()
        self._day_check_job = self.after(60_000, self._check_new_day)

    def destroy(self):
        """Cancel the once-a-minute timer so nothing runs after the window closes."""
        if self._day_check_job is not None:
            try:
                self.after_cancel(self._day_check_job)
            except Exception:
                pass
            self._day_check_job = None
        super().destroy()

    # ----------------------------------------------------------
    # Helper
    # ----------------------------------------------------------

    def _refresh_folder(self, project_id: int):
        """Redraw one folder's task list + badge after a task change."""
        if project_id in self.folder_cards:
            self.folder_cards[project_id].refresh_tasks()
            self.folder_cards[project_id].refresh_badge()

    # ----------------------------------------------------------
    # Comments (NEW, round 6) -- called by CommentRow / FolderCard
    # ----------------------------------------------------------

    def add_comment(self, project_id: int, text: str):
        """Save a new comment and redraw the folder's comment list."""
        try:
            self.db.add_comment(project_id, text)
        except Exception as e:
            logger.error(f"Error adding comment: {e}")
            messagebox.showerror("Error", "Failed to add comment.")
        self._refresh_comments(project_id)

    def edit_comment(self, project_id: int, comment_id: int, text: str):
        """Save the new text of an existing comment."""
        if not self.db.update_comment(comment_id, text):
            messagebox.showerror("Error", "Failed to update comment.")
        self._refresh_comments(project_id)

    def delete_comment(self, project_id: int, comment_id: int):
        """
        Ask, delete, then redraw. Redrawing is what RENUMBERS the remaining
        comments: the number is just the position in the list.
        """
        if not messagebox.askyesno("Delete comment", "Delete this comment?", icon="warning"):
            return
        if self.db.delete_comment(comment_id):
            self._refresh_comments(project_id)
        else:
            messagebox.showerror("Error", "Failed to delete comment.")

    def discard_comment_draft(self, project_id: int, row):
        """A new comment was left empty / cancelled: remove it. Nothing was saved."""
        row.destroy()
        if project_id in self.folder_cards:
            self.folder_cards[project_id]._update_comments_visibility()

    def _refresh_comments(self, project_id: int):
        if project_id in self.folder_cards:
            self.folder_cards[project_id].refresh_comments()

# ============================================================
# calendar_popup.py  —  Small themed date picker (NEW FILE)
# ============================================================
# WHY THIS FILE EXISTS:
#   CustomTkinter has no calendar widget. Instead of adding a
#   dependency (tkcalendar draws old-style ttk widgets that do not
#   follow CTk's light/dark switch), this popup is built ONLY from
#   normal CTk widgets and Python's built-in `calendar` module.
#   Because it uses the colour tokens from theme.py, it automatically
#   matches the app in both dark and light mode.
#
# HOW IT IS USED (same popup for adding AND editing a deadline):
#   CalendarPopup(
#       master,                      # any widget; its window is the parent
#       initial=date(2026, 12, 31),  # date to pre-select, or None
#       on_select=my_function,       # called with a `date`, or None for "Clear"
#       anchor=some_button,          # popup opens just below this widget
#   )
#   Closing the popup with Cancel / Escape / the window's X button
#   does NOT call on_select, so nothing changes.
# ============================================================

import calendar
from datetime import date, timedelta
from typing import Callable, Optional

import customtkinter as ctk
import tkinter as tk

from theme import (
    FONT_LG, FONT_MD, FONT_SM,
    TRANSPARENT,
    PAD_XS, PAD_MD,
    RADIUS_BTN
)
# NEW (round 6): colours come from settings.py.
from settings import (
    ACCENT, ACCENT_HOVER,
    DANGER,
    TEXT_PRIMARY, TEXT_SECONDARY,
    SURFACE_HOVER,
    CALENDAR_SELECTED_TEXT
)

# 0 = Monday, 6 = Sunday. Change this one number to start the week on
# Sunday instead. (calendar.Calendar uses the same numbering.)
FIRST_WEEKDAY = 0


class CalendarPopup(ctk.CTkToplevel):
    """
    A month grid with previous / next arrows.

    • Clicking a day picks it immediately and closes the popup.
    • "Today" picks today's date.
    • "Clear" reports None (= remove the deadline); only shown when
      allow_clear is True.
    • Days from the neighbouring months are shown muted so every
      month always fills a full 6-row grid and the popup never
      changes size while you flip months.
    """

    def __init__(self, master,
                 initial: Optional[date] = None,
                 on_select: Optional[Callable[[Optional[date]], None]] = None,
                 anchor: Optional[tk.Widget] = None,
                 allow_clear: bool = True):
        super().__init__(master)
        self.title("Select deadline")
        self.resizable(False, False)

        self.on_select = on_select
        self.selected = initial                  # the date currently highlighted (or None)

        # The month being DISPLAYED. Start on the selected date's month,
        # or on the current month when nothing is selected yet.
        start = initial or date.today()
        self.view_year = start.year
        self.view_month = start.month

        # Escape = cancel. The window's own X button also just closes it.
        self.bind("<Escape>", lambda e: self.destroy())
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        self._build_header()
        self._build_grid()
        self._build_footer(allow_clear)
        self._render()

        # Place the popup next to the widget that opened it.
        self._position(master, anchor)

        # Behave like a modal dialog (blocks the main window until closed).
        # grab_set() raises TclError if the window is not visible yet on some
        # systems, so it is deferred slightly and wrapped in try/except.
        self.after(50, self._make_modal)

    # ----------------------------------------------------------
    # Building the widgets (done once; _render() only updates text/colours)
    # ----------------------------------------------------------

    def _build_header(self):
        """Row with  ‹  Month Year  ›  navigation."""
        header = ctk.CTkFrame(self, fg_color=TRANSPARENT)
        header.grid(row=0, column=0, sticky="ew", padx=PAD_MD, pady=(PAD_MD, PAD_XS))
        header.grid_columnconfigure(1, weight=1)    # month label takes the free space

        ctk.CTkButton(
            header, text="‹", width=30, height=30, font=FONT_LG,
            fg_color=TRANSPARENT, text_color=TEXT_PRIMARY,
            hover_color=SURFACE_HOVER, corner_radius=RADIUS_BTN,
            command=lambda: self._shift_month(-1)
        ).grid(row=0, column=0)

        self.month_lbl = ctk.CTkLabel(header, text="", font=FONT_LG, text_color=TEXT_PRIMARY)
        self.month_lbl.grid(row=0, column=1)

        ctk.CTkButton(
            header, text="›", width=30, height=30, font=FONT_LG,
            fg_color=TRANSPARENT, text_color=TEXT_PRIMARY,
            hover_color=SURFACE_HOVER, corner_radius=RADIUS_BTN,
            command=lambda: self._shift_month(+1)
        ).grid(row=0, column=2)

    def _build_grid(self):
        """Weekday captions + a 6x7 block of day buttons."""
        grid = ctk.CTkFrame(self, fg_color=TRANSPARENT)
        grid.grid(row=1, column=0, padx=PAD_MD, pady=PAD_XS)

        # Weekday captions: "Mo Tu We ..." (two letters of the English abbreviation)
        for col in range(7):
            name = calendar.day_abbr[(FIRST_WEEKDAY + col) % 7][:2]
            ctk.CTkLabel(
                grid, text=name, font=FONT_SM, text_color=TEXT_SECONDARY, width=34
            ).grid(row=0, column=col, pady=(0, PAD_XS))

        # 42 buttons (6 weeks x 7 days). They are created once and re-used
        # every time the month changes; _render() only edits their text/colour.
        self.day_buttons = []
        for row in range(6):
            for col in range(7):
                btn = ctk.CTkButton(
                    grid, text="", width=34, height=30, font=FONT_MD,
                    corner_radius=RADIUS_BTN, fg_color=TRANSPARENT
                )
                btn.grid(row=row + 1, column=col, padx=1, pady=1)
                self.day_buttons.append(btn)

    def _build_footer(self, allow_clear: bool):
        """Clear / Today / Cancel buttons."""
        footer = ctk.CTkFrame(self, fg_color=TRANSPARENT)
        footer.grid(row=2, column=0, sticky="ew", padx=PAD_MD, pady=(PAD_XS, PAD_MD))
        footer.grid_columnconfigure(1, weight=1)    # pushes Today/Cancel to the right

        if allow_clear:
            ctk.CTkButton(
                footer, text="Clear", width=64, height=30, font=FONT_SM,
                fg_color=TRANSPARENT, text_color=DANGER,
                hover_color=SURFACE_HOVER, corner_radius=RADIUS_BTN,
                command=lambda: self._finish(None)       # None = "remove deadline"
            ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            footer, text="Today", width=64, height=30, font=FONT_SM,
            fg_color=ACCENT, hover_color=ACCENT_HOVER, corner_radius=RADIUS_BTN,
            command=lambda: self._finish(date.today())
        ).grid(row=0, column=2, padx=(0, PAD_XS))

        ctk.CTkButton(
            footer, text="Cancel", width=64, height=30, font=FONT_SM,
            fg_color=TRANSPARENT, text_color=TEXT_SECONDARY,
            hover_color=SURFACE_HOVER, corner_radius=RADIUS_BTN,
            command=self.destroy                         # no callback -> nothing changes
        ).grid(row=0, column=3)

    # ----------------------------------------------------------
    # Drawing the current month
    # ----------------------------------------------------------

    def _render(self):
        """Refresh the month title and all 42 day buttons."""
        self.month_lbl.configure(
            text=f"{calendar.month_name[self.view_month]} {self.view_year}"
        )

        # First cell of the grid = the first "week start" on or before the 1st
        # of the displayed month. monthdatescalendar() gives whole weeks and
        # its first date is exactly that cell.
        weeks = calendar.Calendar(firstweekday=FIRST_WEEKDAY).monthdatescalendar(
            self.view_year, self.view_month
        )
        first_cell = weeks[0][0]
        today = date.today()

        for index, btn in enumerate(self.day_buttons):
            day = first_cell + timedelta(days=index)      # one date per cell, 42 in a row
            in_month = (day.month == self.view_month)
            is_selected = (self.selected == day)
            is_today = (day == today)

            if is_selected:
                # Selected day: solid accent colour with white text.
                btn.configure(
                    text=str(day.day), fg_color=ACCENT, hover_color=ACCENT_HOVER,
                    text_color=CALENDAR_SELECTED_TEXT, border_width=0
                )
            else:
                # Normal day. Today gets a thin accent outline so it is easy to find;
                # days of neighbouring months are muted.
                btn.configure(
                    text=str(day.day), fg_color=TRANSPARENT, hover_color=SURFACE_HOVER,
                    text_color=TEXT_PRIMARY if in_month else TEXT_SECONDARY,
                    border_width=1 if is_today else 0,
                    border_color=ACCENT
                )

            # Bind THIS cell's date to the click. The `d=day` default argument
            # is essential: without it every button would end up using the
            # LAST value of `day` from the loop.
            btn.configure(command=lambda d=day: self._finish(d))

    def _shift_month(self, delta: int):
        """Move the view one month back (-1) or forward (+1), wrapping the year."""
        month_index = self.view_year * 12 + (self.view_month - 1) + delta
        self.view_year, month0 = divmod(month_index, 12)
        self.view_month = month0 + 1
        self._render()

    # ----------------------------------------------------------
    # Finishing / placement helpers
    # ----------------------------------------------------------

    def _finish(self, chosen: Optional[date]):
        """Report the choice to the caller, then close the popup."""
        try:
            if self.on_select:
                self.on_select(chosen)
        finally:
            # Close even if the callback raised, so the popup can never get stuck.
            self.destroy()

    def _make_modal(self):
        """Grab input focus so the main window waits for this popup."""
        try:
            self.lift()
            self.grab_set()
            self.focus_set()
        except tk.TclError:
            # Window already closed or not viewable: modality is a nicety, not a must.
            pass

    def _position(self, master, anchor: Optional[tk.Widget]):
        """
        Open just below `anchor` (the button that was clicked), flipping above
        it or sliding left if the popup would run off the screen. Without an
        anchor, centre the popup over the main window.
        """
        self.update_idletasks()                       # make sure the size is known
        width, height = self.winfo_reqwidth(), self.winfo_reqheight()
        screen_w, screen_h = self.winfo_screenwidth(), self.winfo_screenheight()

        if anchor is not None:
            x = anchor.winfo_rootx()
            y = anchor.winfo_rooty() + anchor.winfo_height() + PAD_XS
            if y + height > screen_h - 48:            # not enough room below -> open above
                y = anchor.winfo_rooty() - height - PAD_XS
        else:
            top = master.winfo_toplevel()
            x = top.winfo_rootx() + (top.winfo_width() - width) // 2
            y = top.winfo_rooty() + (top.winfo_height() - height) // 2

        x = max(0, min(x, screen_w - width - 8))
        y = max(0, min(y, screen_h - height - 8))
        self.geometry(f"+{x}+{y}")

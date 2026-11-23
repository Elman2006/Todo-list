# ============================================================
# top_frame.py  —  App header bar (title + theme toggle)
# ============================================================

import customtkinter as ctk
from theme import (
    FONT_XL, FONT_SM,
    PAD_MD, PAD_LG
)
# NEW (round 6): colours come from settings.py. (This file is not used by the
# app any more; its imports were only updated so it is not left broken.)
from settings import ACCENT, TEXT_SECONDARY


class TopFrame(ctk.CTkFrame):
    """
    The thin header bar at the very top of the window.

    Contains:
      • App title on the left
      • Light / Dark mode toggle on the right

    Layout note: TopFrame configures only ITS OWN grid columns.
    The parent window's grid is configured in main.py — that is
    the correct place for it (root cause fix).
    """

    def __init__(self, master, current_theme: str):
        # fg_color="transparent" means the frame blends into the
        # window background instead of drawing a coloured box.
        super().__init__(master, fg_color="transparent")

        # Place this frame in row 0 of the parent's grid.
        # sticky="ew" makes it stretch left-to-right.
        self.grid(row=0, column=0, sticky="ew", padx=PAD_LG, pady=(PAD_MD, 0))

        # Column 0 (title) expands; column 1 (toggle) stays fixed
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        # ------ App title ------------------------------------------
        self.title_lbl = ctk.CTkLabel(
            self,
            text="✦  Task Manager",   # Small icon adds personality
            font=FONT_XL,
            text_color=TEXT_SECONDARY
        )
        self.title_lbl.grid(row=0, column=0, sticky="w", pady=PAD_MD)

        # ------ Theme toggle ---------------------------------------
        # StringVar holds the current theme value ("dark" / "light")
        # so the switch widget and our logic stay in sync.
        self.switch_var = ctk.StringVar(value=current_theme)

        self.theme_switch = ctk.CTkSwitch(
            self,
            text="",                       # Label is set dynamically below
            command=self._on_toggle,
            variable=self.switch_var,
            onvalue="light",
            offvalue="dark",
            button_color=ACCENT,
            button_hover_color=ACCENT,
            progress_color=ACCENT
        )
        self.theme_switch.grid(row=0, column=1, sticky="e", pady=PAD_MD)

        # Separate label next to the switch — cleaner than putting
        # text on the switch widget itself
        self.theme_label = ctk.CTkLabel(
            self,
            text=self._theme_label(current_theme),
            font=FONT_SM,
            text_color=TEXT_SECONDARY
        )
        self.theme_label.grid(row=0, column=2, sticky="e", padx=(PAD_MD, 0), pady=PAD_MD)

    # ----------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------

    def _theme_label(self, theme: str) -> str:
        """Return a readable label string for the current theme."""
        return "☀  Light" if theme == "light" else "🌙  Dark"

    def _on_toggle(self):
        """
        Called every time the switch is flipped.

        Reads the current StringVar value, applies the new
        appearance mode, and updates the label text.
        """
        new_theme = self.switch_var.get()   # "light" or "dark"
        ctk.set_appearance_mode(new_theme)
        self.theme_label.configure(text=self._theme_label(new_theme))

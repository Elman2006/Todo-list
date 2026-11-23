# ============================================================
# icons.py  —  Loads, tints and displays the PNG icons (NEW FILE)
# ============================================================
# WHY THIS FILE EXISTS:
#   The pen / trash / calendar / copy / bell icons are Lucide icons
#   (ISC licence, see icons/LICENSE.txt), shipped as 36 px WHITE PNGs in
#   the icons/ folder. CustomTkinter shows them through CTkImage, which
#   needs only Pillow (already installed with customtkinter) -- no SVG
#   library and no native DLLs.
#
#   Because the PNGs are plain white, ONE file can be shown in any colour:
#   this module recolours the file at runtime (resting, hover, disabled...).
#   That is why only 7 files are needed instead of 7 x every colour.
#
# WHAT IS IN HERE:
#   icon_image()     -> a tinted, cached CTkImage for an icon name
#   IconButton       -> a small rounded button showing one icon, with a
#                       hover colour, a "locked" (greyed) state and a
#                       temporary "flash" (used for the copy confirmation)
# ============================================================

import os
import logging

import customtkinter as ctk
from PIL import Image

from theme import (
    FONT_FAMILY,
    TRANSPARENT,
    ICON_SIZE, ICON_BTN_SIZE,
    RADIUS_BTN
)
# NEW (round 6): colours come from settings.py.
from settings import (
    ACCENT, SURFACE_SELECTED,
    ICON_IDLE, ICON_DISABLED
)

logger = logging.getLogger(__name__)


# The icons/ folder sits next to this file (the app runs directly from source).
ICON_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")

# Plain-text stand-ins, used ONLY if an icon file is missing, so the app
# still runs and the button is still clickable.
FALLBACK_GLYPH = {
    "pencil": "Edit", "trash": "Del", "calendar": "Date",
    "copy": "Copy", "bell": "Bell", "bell-off": "Mute", "check": "OK",
}

_alpha_cache = {}    # icon name -> the PNG's transparency layer (loaded once)
_image_cache = {}    # (name, light colour, dark colour, size) -> CTkImage
_warned_missing = set()


def _alpha_of(name: str):
    """Load icons/<name>.png once and keep only its transparency layer."""
    if name not in _alpha_cache:
        path = os.path.join(ICON_DIR, f"{name}.png")
        with Image.open(path) as image:
            _alpha_cache[name] = image.convert("RGBA").getchannel("A")
    return _alpha_cache[name]


def _tint(name: str, hex_colour: str):
    """A solid-colour copy of the icon: the colour comes from us, the shape from the PNG."""
    alpha = _alpha_of(name)
    tinted = Image.new("RGBA", alpha.size, hex_colour)
    tinted.putalpha(alpha)
    return tinted


def icon_image(name: str, colour, size: int = ICON_SIZE):
    """
    Return a CTkImage of icon `name` in `colour`, or None if the file is missing.

    `colour` is either one hex string ("#A6A6A6") or a (light mode, dark mode)
    pair -- the same convention the rest of the app uses for colours.
    Results are cached; the cache also keeps every image referenced, which
    matters because tkinter would otherwise garbage-collect them and the
    icons would silently disappear.
    """
    light, dark = (colour, colour) if isinstance(colour, str) else colour
    key = (name, light, dark, size)
    if key not in _image_cache:
        try:
            _image_cache[key] = ctk.CTkImage(
                light_image=_tint(name, light),
                dark_image=_tint(name, dark),
                size=(size, size)
            )
        except (FileNotFoundError, OSError):
            if name not in _warned_missing:
                _warned_missing.add(name)
                logger.warning("Icon file icons/%s.png not found - showing text instead.", name)
            return None
    return _image_cache[key]


class IconButton(ctk.CTkButton):
    """
    A rounded, transparent button that shows one icon.

    States:
      - resting : icon in the `idle` colour
      - hover   : icon in the `hover` colour + a soft background (CTkButton does the background)
      - locked  : greyed icon, click does nothing (used by the "adding a task" lock)

    Example:  IconButton(parent, "pencil", command=self.rename)
    """

    def __init__(self, master, icon: str, command=None,
                 idle=ICON_IDLE, hover=ACCENT, disabled=ICON_DISABLED,
                 hover_bg=SURFACE_SELECTED,
                 size: int = ICON_SIZE, button_size: int = ICON_BTN_SIZE):

        image = icon_image(icon, idle, size)
        super().__init__(
            master,
            text="" if image is not None else FALLBACK_GLYPH.get(icon, "?"),
            image=image,
            font=(FONT_FAMILY, 11),
            text_color=idle,                # only visible when the icon file is missing
            width=button_size, height=button_size,
            fg_color=TRANSPARENT,
            hover_color=hover_bg,
            corner_radius=RADIUS_BTN,
            command=command
        )
        self._ib_icon = icon
        self._ib_idle = idle
        self._ib_hover = hover
        self._ib_disabled = disabled
        self._ib_size = size
        self._ib_hovering = False
        self._ib_flash_job = None
        self.lock_active = False            # public: True while the button is greyed out

        # bind() on a CTk widget ADDS to its built-in hover handling.
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    # ----------------------------------------------------------
    # Drawing
    # ----------------------------------------------------------

    def _render(self):
        """Show the icon in the colour that matches the current state."""
        if self.lock_active:
            colour = self._ib_disabled
        elif self._ib_hovering:
            colour = self._ib_hover
        else:
            colour = self._ib_idle
        image = icon_image(self._ib_icon, colour, self._ib_size)
        if image is not None:
            self.configure(image=image)
        else:
            self.configure(text_color=colour)

    def _on_enter(self, event=None):
        self._ib_hovering = True
        if not self.lock_active:
            self._render()

    def _on_leave(self, event=None):
        self._ib_hovering = False
        if not self.lock_active:
            self._render()

    # ----------------------------------------------------------
    # Changing the look from outside
    # ----------------------------------------------------------

    def set_icon(self, icon: str):
        """Swap the picture (for example bell <-> bell-off)."""
        self._ib_icon = icon
        self.configure(text="" if icon_image(icon, self._ib_idle, self._ib_size) else FALLBACK_GLYPH.get(icon, "?"))
        self._render()

    def set_palette(self, idle=None, hover=None, hover_bg=None):
        """Change colours, e.g. when the folder header changes its status colour."""
        if idle is not None:
            self._ib_idle = idle
        if hover is not None:
            self._ib_hover = hover
        if hover_bg is not None:
            self.configure(hover_color=hover_bg)
        self._render()

    def set_locked(self, locked: bool):
        """Grey the icon out and make clicks do nothing (or undo that)."""
        self.lock_active = locked
        self.configure(state="disabled" if locked else "normal")
        self._render()

    def flash(self, icon: str, colour, milliseconds: int = 1200):
        """
        Show `icon` in `colour` for a moment, then go back to normal.
        Used for the green check after "copy", instead of a dialog box.
        """
        if self._ib_flash_job is not None:          # a second click restarts the timer
            self.after_cancel(self._ib_flash_job)
        else:
            self._ib_before = (self._ib_icon, self._ib_idle, self._ib_hover)   # remember the normal look
        self._ib_icon, self._ib_idle, self._ib_hover = icon, colour, colour
        self._render()
        self._ib_flash_job = self.after(milliseconds, self._end_flash)

    def _end_flash(self):
        self._ib_flash_job = None
        self._ib_icon, self._ib_idle, self._ib_hover = self._ib_before
        self._render()

    def destroy(self):
        """Never leave a timer running for a button that no longer exists."""
        if self._ib_flash_job is not None:
            try:
                self.after_cancel(self._ib_flash_job)
            except Exception:
                pass
            self._ib_flash_job = None
        super().destroy()

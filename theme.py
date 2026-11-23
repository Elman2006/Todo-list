# ============================================================
# theme.py  —  Central Design System
# ============================================================
# WHY THIS FILE EXISTS:
#   Previously every widget used CustomTkinter defaults (Arial,
#   plain gray, no consistent spacing).  By putting ALL visual
#   constants here, changing one value updates the whole app.
# ============================================================
# UPDATE (round 6): ALL COLOURS now live in settings.py. This file keeps the
# fonts, spacing, corner radii and sizes. The comments of the colour blocks
# were moved to settings.py together with their values, unchanged.
# ============================================================

# ------ Font family ----------------------------------------
# "Segoe UI" ships on Windows; macOS falls back to "SF Pro
# Display"; Linux falls back to "DejaVu Sans".  All are better
# than Arial.  CustomTkinter accepts a tuple: (family, size).
FONT_FAMILY = "Segoe UI"

# ------ Font scale -----------------------------------------
# Define every size in ONE place so the hierarchy is obvious.
FONT_XL    = (FONT_FAMILY, 20, "bold")   # App title
FONT_LG    = (FONT_FAMILY, 15, "bold")   # Section headers
FONT_MD    = (FONT_FAMILY, 13)           # Body / buttons
FONT_SM    = (FONT_FAMILY, 11)           # Captions / meta text

# ------ Spacing (pixels) -----------------------------------
# Consistent padding units keep everything aligned.
PAD_XS = 4
PAD_SM = 8
PAD_MD = 12
PAD_LG = 18

# ------ Corner radius --------------------------------------
# Unified roundness for all buttons and cards.
RADIUS_BTN  = 8
RADIUS_CARD = 10


# ------ Transparent helper --------------------------------
# Used for buttons that should look like text/links.
TRANSPARENT = "transparent"

# ------ NEW: tokens added for the folder/accordion UI ------
# Slightly larger radius than RADIUS_CARD gives folder headers a
# softer, more "modern" feel without changing existing widgets
# that already use RADIUS_CARD.
RADIUS_LG = 12


# ------ NEW (polish round): larger deadline + three-dots menu --
# Kept here, like every other size, so they can be tuned in ONE place.

# Deadline cell: bigger than FONT_SM (11) so it can be read at a glance.
FONT_DEADLINE      = (FONT_FAMILY, 13)            # "18 days left"
FONT_DEADLINE_BOLD = (FONT_FAMILY, 13, "bold")    # the date itself stands out

# The "•••" button glyph (was 12 bold). Larger dots = easier to see and click.
FONT_MENU_BTN  = (FONT_FAMILY, 17, "bold")

# Text inside the drop-down list (Edit / Rename / Delete). This is a native
# tk.Menu, which only supports a font change, not themed corners or colours.
FONT_MENU_LIST = (FONT_FAMILY, 12)

# Click target of the "•••" button, in pixels (was 28 x 28).
MENU_BTN_WIDTH  = 40
MENU_BTN_HEIGHT = 36

# ============================================================
# ROUND 4 additions: icon buttons + project-status colours (NEW)
# Nothing above this line was changed.
# ============================================================

# ------ Icon sizes -------------------------------------------
# The PNG files in the icons/ folder are 36 px wide (@2x); they are DRAWN at
# ICON_SIZE px, so they stay sharp on high-DPI screens. ICON_BTN_SIZE is the
# size of the clickable rounded button around each icon.
ICON_SIZE     = 18
ICON_BTN_SIZE = 34

# ------ NEW (round 6): font of the comments --------------------
# Comments are shown in italics. (Their COLOUR is COMMENT_TEXT in settings.py.)
FONT_COMMENT = (FONT_FAMILY, 13, "italic")

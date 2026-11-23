# ============================================================
# settings.py  —  ALL colours of the app, in ONE place  (NEW FILE)
# ============================================================
# THIS IS A PLAIN PYTHON FILE. To change a colour: edit the value here, save,
# and start the app again (python main.py). No other file needs to be touched.
#
# WHY ONE FILE ("single source of truth"):
#   Every colour the app uses is defined here and nowhere else; all other
#   files only IMPORT these names. So a colour can never be "half changed",
#   and you never have to hunt through the code for a hex value.
#
# HOW A COLOUR IS WRITTEN
#   one value   "#4F8EF7"
#   or a pair   ("light mode colour", "dark mode colour")
#   The app always runs in dark mode, so the SECOND value of a pair is the one
#   you see; the first is kept so a light mode could be switched on again.
#   Values are hex codes ("#RRGGBB") or Tk colour names ("gray17", "white").
#   EXCEPTION: the ICON_* colours must be hex codes -- they are used to tint the
#   icon pictures, and the picture library does not understand names like "gray50".
#
# THE FILE HAS FOUR PARTS
#   1. STATUS COLOUR-CODING  the red / orange / green project title background
#                            (and the single flag that switches it off)
#   2. FONT COLOURS          titles, helper text, comments, overdue/feedback text
#   3. BUTTON COLOURS        buttons, icons, checkboxes, menus, the calendar
#   4. FRAME COLOURS         cards, headers, borders, separators
#
# The default values are exactly the colours the app had before this file
# existed, so nothing looks different until you change something.
# ============================================================

# ============================================================
# 1. STATUS COLOUR-CODING  (project title background)
# ============================================================

# NEW (round 6): ONE flag to turn the colour-coding off.
#   True  = a project's title background shows how far its tasks are:
#           green = all done, orange = some done, red = none done,
#           neutral grey = the project has no tasks.
#   False = every project title keeps the neutral (grey) background, whatever
#           its tasks look like. (Everything else is unchanged; the task counter
#           such as "2 / 5" is still shown.)
STATUS_COLORS_ENABLED = True

# ------ Project header colours = task completion ---------------
# Muted shades that sit comfortably on the dark window. Each background has
# a slightly lighter HOVER variant, which is also used while the folder is
# expanded ("selected"). Every text and icon colour below was measured with
# the WCAG contrast formula: at least 4.5:1 on every background, base and
# hover, in dark mode (the mode the app now always uses).
STATUS_DONE_BG     = ("#BFE3CC", "#2E5A43")   # green  = every task done
STATUS_DONE_HOVER  = ("#AEDABF", "#34664C")
STATUS_SOME_BG     = ("#F2D9B0", "#7A5120")   # orange = some tasks done
STATUS_SOME_HOVER  = ("#EBCB98", "#855A27")
STATUS_NONE_BG     = ("#EBC3C3", "#6E3535")   # red    = no task done
STATUS_NONE_HOVER  = ("#E3B0B0", "#7A3B3B")

STATUS_TEXT         = ("#1B1B1B", "#F5F5F5")  # folder name + date on a coloured header
STATUS_TEXT_MUTED   = ("#3A3A3A", "#E6E6E6")  # badge, "days left", divider
STATUS_OVERDUE_TEXT = ("#8A1C1C", "#FFD6D6")  # overdue text (plain red is unreadable on a red header)

# ============================================================
# 2. FONT COLOURS
# ============================================================

# ------ Neutral text colours (light / dark pair) ----------
TEXT_PRIMARY   = ("gray10",  "gray95")   # Main readable text
TEXT_SECONDARY = ("gray45",  "gray60")   # Muted / helper text

# Muted colour for small icon-like glyphs: the expand/collapse
# arrow and the "•••" menu button.
ICON_MUTED = ("gray50", "gray55")

# ------ Success colour (completion feedback) --------------
SUCCESS = "#4CAF7D"

# ------ NEW (round 6): colour of the comment text ----------------
# Comments (the numbered notes at the top of an open project) are shown in
# italics in THIS colour. It is deliberately different from the task title
# (TEXT_PRIMARY above) and from the preview of a task's details (TEXT_SECONDARY).
COMMENT_TEXT = ("#5B3FA0", "#B9A6E8")      # soft lavender

# ------ NEW (round 6): title of a finished task -----------------
# This used to be written directly in mid_frame.py; same value, now here.
COMPLETED_TASK_TEXT = "gray55"             # a ticked-off task (also struck through)

# ============================================================
# 3. BUTTON COLOURS
# ============================================================

# ------ Accent colour --------------------------------------
# One accent colour used for primary actions.  Override here
# to re-skin the entire app instantly.
ACCENT       = "#4F8EF7"   # Calm blue
ACCENT_HOVER = "#2D6FD4"   # Darker on hover

# ------ Danger colour (delete actions) --------------------
DANGER       = "#E05252"
DANGER_HOVER = "#B03030"

# ------ Icon tints (light mode, dark mode) --------------------
# The icon PNGs are plain white; icons.py recolours them at runtime. Pillow
# needs real hex colours here (it does not understand Tk names like "gray50").
ICON_IDLE          = ("#6E6E6E", "#A6A6A6")   # resting icon on a normal (grey) row
ICON_DISABLED      = ("#C4C4C4", "#555555")   # greyed-out / locked icon
ICON_ON_BAND       = ("#3A3A3A", "#EDEDED")   # resting icon on a status-coloured header
ICON_ON_BAND_HOVER = ("#000000", "#FFFFFF")   # hovered icon on a status-coloured header
ICON_DANGER_ON_BAND_HOVER = ("#8A1C1C", "#FFD6D6")   # hovered trash icon on a coloured header

# Soft red background for a hovered trash button (the blue one is SURFACE_SELECTED).
DANGER_SOFT = ("#F6D8D8", "#4A2828")

# ------ Round 4, batch 2: bell + "adding a task" lock --------
# Icon colours for a MUTED bell (the bell-with-slash): dimmer than a normal
# icon but still clearly visible. First = on a status-coloured header,
# second = on the neutral header.
ICON_DIM_ON_BAND = ("#6A6A6A", "#C4C4C4")
ICON_DIM         = ("#9A9A9A", "#7A7A7A")

# Look of a greyed-out (locked) text button, e.g. "Add Folder" while a task
# is being typed: flat grey background and grey text.
LOCKED_BG   = ("gray78", "gray28")
LOCKED_TEXT = ("gray50", "gray55")

# ------ NEW (round 6): colours that used to be written inside the code ------
# These three were plain literals in mid_frame.py and calendar_popup.py. They are
# here now, with exactly the same values, so that every colour lives in this file.
CHECKMARK              = "white"   # the tick inside a checked task checkbox
MENU_ACTIVE_TEXT       = "white"   # text of the highlighted entry in the right-click menu
CALENDAR_SELECTED_TEXT = "white"   # day number of the selected day in the date picker

# ============================================================
# 4. FRAME COLOURS
# ============================================================

# ------ Card / surface colours ----------------------------
# These are (light_mode_colour, dark_mode_colour) tuples that
# CustomTkinter interprets automatically.
SURFACE        = ("gray92", "gray17")   # Card background
SURFACE_HOVER  = ("gray85", "gray22")   # Card hover state
SURFACE_SELECTED = ("#D6E6FF", "#1E3A5F")  # Active project highlight

# Faint border so folder cards read as distinct containers even
# when their fill colour is close to the window background.
BORDER_SUBTLE = ("gray78", "gray28")

# Slightly different hover tone for folder headers only, so a
# hovered header is distinguishable from a hovered task row.
HEADER_HOVER = ("gray88", "gray20")

# ------ NEW (round 6): window separator -------------------------
# The thin line between the project list and the "New folder" bar (main.py).
SEPARATOR = ("gray80", "gray25")

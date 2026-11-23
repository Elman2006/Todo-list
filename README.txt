TASK MANAGER  -  USER GUIDE
===========================

A small desktop app for keeping projects ("folders") and the tasks inside
them. Built with Python, CustomTkinter and SQLite. Everything is saved
automatically; there is no Save button.


1. HOW TO RUN
-------------
You need Python 3.9 or newer and one package:

    pip install customtkinter

(customtkinter also installs Pillow, which the icons need.)

Keep these files together in ONE folder:

    main.py  mid_frame.py  bottom_frame.py  database.py  calendar_popup.py
    icons.py  theme.py  settings.py  app.ico  and the folder  icons/

Start the program from that folder:

    python main.py

The app runs directly from the source files: there is no build step, no
installer and no .exe version (packaging is not part of this project).

The database file projects.db is created automatically in the folder you
start the program from, so it sits next to the source files. To move your
data to another computer, copy projects.db. The app always uses the dark theme.


2. FOLDERS (PROJECTS) AND TASKS
-------------------------------
Add a folder   Type a name in the bar at the bottom, press Enter or click
               "Add Folder". The new folder appears at the top and opens.
Open / close   Click a folder's header or its small arrow.
Add a task     Open the folder and type in the "New task..." box at the TOP of
               its list, then press Enter or click "Add Task". New tasks appear at
               the top of the list. Press Esc to throw a half-typed task away.
Done           Tick the checkbox in front of a task; it is struck through.
Rename         Pen icon (folder or task). You can also double-click a name, or
               right-click it and choose the entry from the menu.
Task details   The pen icon on a task opens a window with a title and an
               optional "Details" box. A short preview of the details (the
               first 6 whole words, followed by ... if there is more) is shown
               in small grey text right after the task title.
Delete         Trash icon. You are asked to confirm. Deleting a folder also
               deletes all of its tasks.


3. COMMENTS
-----------
Every project can have a list of comments: short notes about the project as a
whole (not about one task).
- They are at the very TOP of the open project, above the "New task..." box and
  the tasks. They only show while the project is open, and a project without
  comments shows nothing at all there.
- Click "Add Comment" (next to "Add Task"). A new empty comment appears at the
  end of the list, ready to type into right there. Enter saves it, Shift+Enter
  starts a new line, Esc cancels. A comment you leave empty is not kept.
- The pen icon edits a comment in place (Enter or the check mark saves, Esc
  cancels), the trash icon deletes it (you are asked first), and the copy icon
  puts ONLY the comment text on the clipboard.
- Comments are numbered 1, 2, 3 ... in the order they were added, in italics and
  in their own colour. The numbers cannot be edited and comments cannot be
  moved. If you delete a comment, the ones after it are renumbered.
- Comments are saved in projects.db, and they are deleted together with their
  project.


4. DEADLINES
------------
A deadline is optional.
- When adding a folder, click "Deadline" next to the name box, pick a day in
  the calendar, then add the folder. The small x next to it removes the date
  again.
- To set, change or remove it later, click the calendar icon on the folder
  (or click the date itself). In the calendar: click a day to pick it,
  "Today" picks today, "Clear" removes the deadline, "Cancel" / Esc changes
  nothing.
- Each folder shows the date and, beside it, how many days are left:
  "17 days left", "1 day left", "Due today", "3 days overdue".
  Days left are recalculated every time the program starts, and again after
  midnight if the program stays open.


5. THE BELL (DEADLINE REMINDERS)
--------------------------------
Every time the program starts it checks all folders and, if needed, shows ONE
message listing them, most urgent first:

    7 days or less left          warning
    2 days or less, or overdue   error (the message box shows the error icon)

The bell icon next to a folder's deadline switches reminders for THAT folder
on or off. A bell = reminders on. A bell with a slash (and a dimmer look) =
muted. Muted folders are only left out of the reminder message; nothing else
about them changes. Your choice is saved. Folders without a deadline are
never listed.


6. COLOUR CODING
----------------
The coloured bar at the top of each folder shows how far its tasks are:

    Green     every task is done
    Orange    some tasks are done
    Red       no task is done yet
    Grey      the folder has no tasks

The colour updates by itself when you tick, add or delete a task. Overdue
dates are shown in a light red so they stay readable on the coloured bar.
An open folder, or the folder under the mouse pointer, is drawn slightly
lighter.

The colours (and an on/off switch for this colour coding) are in settings.py:
see section 11.


7. DRAG AND DROP
----------------
Grab the three-line handle (the "hamburger" icon) next to a folder name to
move the whole folder up or down. Do the same with the handle in front of a
task to reorder the tasks inside their folder. While dragging, hold the
pointer near the top or bottom edge of a long list and it scrolls. The new
order is saved when you let go.


8. THE COPY BUTTON
------------------
The copy icon on a task puts this text on the clipboard:

    <task title>
    <one empty line>
    <task details>

A task without details copies only the title. The icon turns into a green
check mark for a moment to confirm; no window opens. (Copying a COMMENT works
the same way, but copies only the comment text.)


9. "ADDING A TASK" PROTECTION
----------------------------
While you are typing a new task (the box has the cursor AND contains text),
the controls that could pull you away by accident are greyed out and do
nothing: the "Add Folder" button, the "Deadline" button, and each folder's
calendar, pen and trash icons. Task icons and the bell keep working.

They come back as soon as you press Enter, press Esc, empty the box, or click
anywhere else. Clicking a greyed-out button does nothing; the buttons are
active again right after that click, so click once more if you meant it.


10. ICON FILES (the icons/ folder)
----------------------------------
The icons come from the Lucide icon set (https://lucide.dev), licence ISC
(free to use and modify; the notice must stay with the files - it is in
icons/LICENSE.txt). They are stored as small white PNG pictures that the
program recolours itself:

    icons/pencil.png      rename / edit
    icons/trash.png       delete
    icons/calendar.png    edit deadline
    icons/copy.png        copy a task
    icons/bell.png        reminders on
    icons/bell-off.png    reminders muted
    icons/check.png       "copied" confirmation / save a comment
    icons/LICENSE.txt     licence text for the icons

The folder "icons" must sit next to main.py. If a file is missing the program
still works and shows a short text label on that button instead.


11. CHANGING COLOURS (settings.py)
----------------------------------
Every colour of the app is in ONE file, settings.py. It is a plain Python file:
open it in your editor, change a value, save, and start the app again. No other
file needs to be touched. It has four parts:

    1. status colour coding  (the green / orange / red project title background)
    2. font colours          (including the colour of the comments)
    3. button colours        (buttons, icons, checkboxes, menus)
    4. frame colours         (cards, headers, borders, separators)

A colour is one value ("#4F8EF7") or a pair ("light mode", "dark mode"). The
app always runs in dark mode, so the SECOND value of a pair is the one you see.
The ICON_* colours must be hex codes ("#RRGGBB").

To switch the status colour coding OFF, set this single line near the top:

    STATUS_COLORS_ENABLED = False

Every project title then keeps the neutral grey background (the "2 / 5"
counter is still shown). Set it back to True to get the colours again.


12. GOOD TO KNOW
----------------
- The window cannot be made narrower than 800 pixels, so every folder header
  stays readable.
- app.ico is the window icon (shown instead of the default CustomTkinter logo).
- top_frame.py is no longer used (the title bar and light/dark switch were
  removed). You may delete that file.
- Colours: settings.py (section 11). Fonts, spacing and sizes: theme.py. The
  reminder limits are at the top of mid_frame.py (ALERT_WARNING_DAYS = 7 and
  ALERT_ERROR_DAYS = 2 days; the details preview length is PREVIEW_WORDS).

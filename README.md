# OTBMaster3D

A fast 3D chess application designed to make computer chess feel more like
playing over the board. Built for Windows with Python, GLFW, OpenGL, Tkinter,
and python-chess.

Changes:
- remembers camera yaw, pitch and zoom between sessions
- saves camera automatically after rotation/zoom interaction settles
- fixes file labels so they display A to H left-to-right from White's initial view
- keeps rank 1 at the near-left edge
- move panel narrowed
- move history displays numbered move pairs such as `3. d4 d5`
- settings are always fully visible; no expandable/collapsible settings section
- all previous v4 features retained

## Run

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```


v6:
- rank numbers moved to visual left edge
- left-drag on empty board pans the whole board in-plane
- left-drag on a piece still moves that piece
- board pan offsets persist between sessions

v6.1 fix:
- corrected board panning: only the board moves; the camera stays fixed
- left-drag on empty space now visibly pans the board
- pan follows the mouse direction

v7:
- full hyperbullet/bullet/blitz/rapid/classical time-control presets
- Custom time control in seconds + increment
- Online clock mode (automatic switch)
- OTB clock mode: move first, then hit the clock
- selectable OTB clock input: Spacebar, Middle Mouse, Mouse Button 4, Mouse Button 5
- human clock keeps running until the configured clock button is pressed
- engine automatically completes its clock action after moving
- opponent is blocked until the human hits the clock
- OTB clock mode/binding/custom time control persist between sessions

v7.1:
- added Reset Clock button
- custom time fields are hidden unless Custom is selected
- simple left clicks no longer nudge/pan the board
- board panning begins only after a real left-drag threshold is crossed

v7.2:
- Ctrl + left-drag rotates the board exactly like right-drag
- added Reset View button
- Reset View restores default rotation, pitch, pan and zoom without resetting the chess position

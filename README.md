# Google-Minesweeper-Solver

An automated Minesweeper bot built with Python for the Google version of Minesweeper

# Features
- Scans screen to automcatically identify difficulty and initialise the board.
- Utilises patterns, bruteforce, and chunking algorithms to increase success rate.

# Installation
1. Clone the repository:
   ```shell
   git clone https://github.com/losedraw/Google-Minesweeper-Solver.git
   cd Google-Minesweeper-Solver
   ```
2. Install dependencies:
   ```shell
   pip install -r requirements.txt
   ```

# Usage
1. Search Minesweeper on Google and press play.
2. Run `minesweeper.py`.
3. Select your difficulty or leave it on Auto.
4. Make sure your browser zoom is on default settings.
5. Press Start or 'q' to start the solver. Press 'q' again to stop the program.

**Note 1**: The calibration values do not save through different sessions of the program. Make sure to re-calibrate on each launch. I will make this
more convenient in a future update. Sorry for the inconvenience.

**Note 2**: If the program doesn't work, try to use manual calibration and move your mouse to the top-leftmost point of the top-leftmost tile.
Use the arrow keys to adjust your cursor. If it still doesn't work, it might be because your monitor is not 1920x1080. I will fix this in
a future update. Sorry for any inconveniences. You can also try to change the preset values in `minesweeper.py`.

**Note 3**: As you can see, I do not have the RGB values of the numbers 7 and 8. If anyone can find them, that would be of great help.


Use the following global hotkeys:

q: Start / Pause the solver.

z: Select tile coordinate during manual calibration.

esc: Cancel calibration mode.

arrow keys: Adjust the mouse during manual calibration.

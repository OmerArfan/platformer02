## Platform Support

**Current Version:** 1.3.9 (Build 472)

### Windows
- **Windows 11:** Fully Supported.
- **Windows 10:** Supported. (64-bit versions)
- **Older Windows versions(8.1, 7, etc.)**: Not supported. Python 3.11 requires Windows APIs only found in Windows 10 and newer. To prevent confusing crashes, the game is designed to detect older OS versions and display a clear error message.
#### Note: Since this app is from an "Unverified Publisher," Windows SmartScreen may block the initial launch. Click "More Info" and then "Run Anyway" to start the game.

### Linux
- **Ubuntu/Debian-based:** Supported (tested on Linux Mint, Ubuntu and Debian).
- **Arch Linux:** Confirmed Working. (Tested on KDE Plasma). The standalone binary runs smoothly without needing manual library installation.
- **Other Distros:** Untested. Since this is a pre-compiled binary, it may run into library version conflicts on non-Debian systems.
#### Note: If the game doesn't launch on Linux, ensure the file has execution permissions (Right Click > Properties > Allow executing file as program).
#### Tip: To get logs on Linux, run the file via the terminal: ./Roboquix
---

## Troubleshooting & Bug Reports
If you encounter graphical glitches (like screen flickering), crashes, level slowdowns, save/manifest errors, or other types of bugs, please report them in [GitHub Issues](https://github.com/OmerArfan/platformer02/issues).

**Please include:**
1. **OS Version:** (e.g., Ubuntu 24.04, Windows 11 24H2)
2. **Desktop Environment:** If on Linux. (e.g., GNOME, XFCE, KDE)
3. **Hardware:** CPU and GPU (e.g., Ryzen 5 7520U, Radeon 660M)
4. **Logs:** Copy the error text from the terminal/console.
5. **Screenshot if possible:** If it can be of any use, please do send a screenshot of the glitch.
6. **Game/Cleobo Build:** Make sure to add both so that I can verify if the bug has been patched in a newer build. (e.g. Roboquix Build 464, Cleobo Build 13)

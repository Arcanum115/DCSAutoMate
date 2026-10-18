# DCSAutoMate 2.0 Fork
Python scripting engine for DCS World.

> **Kudos to the original developers:** DCSAutoMate was created by [SlipHavoc](https://github.com/SlipHavoc), and nearly all of what makes it work is their design and hard work.  This fork only builds on it.  Please support their work: star and follow the original repo at [SlipHavoc/DCSAutoMate](https://github.com/SlipHavoc/DCSAutoMate), and report bugs and send contributions upstream where they apply.  Thank you, SlipHavoc!

> **Fork notice:** this is [Arcanum115](https://github.com/Arcanum115)'s fork of [SlipHavoc's DCSAutoMate](https://github.com/SlipHavoc/DCSAutoMate), based on DCSAutoMate 2.0.0.  It adds:
> * **F-4E:** once the INS is aligned, both cold starts set weapon select to BOMBS, jettison select to STORES, the reticle to 40 mils and the formation lights on.  Jester sets the radar to active and 25 NM wide, the jammer to transmit and chaff/flares to single, and takes over countermeasures dispensing.
> * **C-130J Cold Start:** APU to RUN right after battery on, a faster ECB reset, and all four engines started together with the throttles held at ground idle.  Also full defensive systems setup, RWR volume, computer drop switch, ARC-210, exterior lighting by day or night, both CNI-MUs and the pilot AMU display layout.  The pilot HUD stays caged.
> * **F-15E Cold Start:** formation lights on bright, WSO CMD on AUTO, VMAX on.
> * **Custom controls:** `config/customControls/` adds read-only controls parsed from cockpit display text, such as the C-130J CNI course and elevation per waypoint.  They show in **Help > Control Reference**.

This program sends commands to DCS via a custom Lua export script (`DCSAutoMateExport.lua`) that talks directly to the game's native control APIs over TCP.  It also uses [pydirectinput](https://github.com/learncodebygaming/pydirectinput) to send keyboard commands.

This is intended to replace the existing built-in autostart scripts in DCS, which after v.2.8 became subject to the "Pure Scripts" flag on multiplayer servers.  In order to modify the built-in startup scripts, you have to change the actual game files, which makes them fail the IC check if Pure Scripts is enabled.  DCSAutoMate is not affected by this check because its commands go through the user-editable Lua export script in Saved Games.

DCSAutoMate can also be used to script any other cockpit commands, such as adding waypoints or setting countermeasures programs.

> **Note on DCS BIOS:** Older versions of DCSAutoMate required [the DCS BIOS fork for DCS Flightpanels](https://github.com/DCSFlightpanels/dcs-bios) as a command channel.  That dependency has been removed.  DCS BIOS is no longer required or used.

# How to use this program

**Updating from a legacy version (1.x, which used DCS BIOS)**

1. Delete the `DCS-BIOS` folder from `C:\Users\<username>\Saved Games\DCS\Scripts`.  (Keep it if another program, such as DCS Flightpanels, Helios or a Stream Deck plugin, still uses it.)
2. Open `Export.lua` in that same folder and remove these two lines:

   ```lua
   dofile(lfs.writedir()..[[Scripts\DCS-BIOS\BIOS.lua]])
   dofile(lfs.writedir()..[[Scripts\DCSAutoMateExport.lua]])
   ```

   You can also delete the old `Scripts\DCSAutoMateExport.lua` file.  DCSAutoMate 2.0 installs its own export script to `Scripts\DCSAutoMate\` and adds its own include line on first run.

**Installation and setup**

1. Download `DCSAutoMate-2.0.0-fork.zip` from this fork's [Releases page](https://github.com/Arcanum115/DCSAutoMate/releases) and extract it to a folder of your choice.  Keep all the files together; the programs look for their data files in their own folder.
2. Run **DCSAutoMate.exe**.  It should detect that the DCSAutoMate script files need to be added to your Saved Games DCS folder and install them automatically.  (You can install or re-install them manually if needed by going to **Settings → Install/Update DCS Scripts...**.)  This also adds an include line to your `Export.lua` if needed.  It will warn you before overwriting existing files.

The exes aren't code-signed, so Windows SmartScreen may warn that it doesn't recognize them the first time you run them.  Click **More info**, then **Run anyway**.

Microsoft Defender finds no threats in the exes, but on VirusTotal a few of the roughly 70 antivirus engines flag them (3 for DCSAutoMate.exe and 4 for DCSControlPanel.exe at upstream's release, all generic or machine-learning detections; this fork's DCSAutoMate.exe is rebuilt, so its count may differ).  This is a known false positive with Python programs packaged into a single exe by PyInstaller.  If you'd rather not trust the exes, you can run DCSAutoMate from the Python source instead (see **Running DCSAutoMate.py as a Python program** below).

**Basic use**

1. Double-click **DCSAutoMate.exe** to run the program.  Keep the DCSAutoMate window open (you can minimize it if you want).
2. Start DCS.
3. When you're in cockpit and ready to run a script, press the hotkey (**Ctrl+Shift+Z** by default) to open the in-game overlay.
4. Select the module (the plane you're in), then the script you want to run, and any options for that script that appear.
5. Click the **Start** button to start running the script.  The script will start sending commands to DCS.
6. After the script is done, you can close the in-game overlay with the same hotkey, or leave it open and ready to run another script.  To stop a script while it's running, click the **Stop** button, or alt-tab out and close the DCSAutoMate window.  While the script is waiting (for a cockpit state, a Loop Until condition, or a timer), **Skip Wait** ends the wait and goes on to the next step.

You can run any script at any time; it's up to you to run the *right* script at the *right* time.

![The DCSAutoMate desktop window after Auto Select picked the FA-18C Cold Start](docs/screenshots/desktopApp.png)

Optionally, you can set a few configuration options for the program by selecting **Tools > Settings...**.  See below for explanation of settings.

**In-Game Interface**

DCSAutoMate 2.0 introduces a new in-game interface (overlay) that allows you to control the program without alt-tabbing out of the game.
* **Hotkey**: Press **Ctrl+Shift+Z** (default) to toggle the overlay.
* **Module Selection**: Automatically detects the current module if possible, or allows manual selection.
* **Script Selection**: Choose from available scripts for the selected module.
* **Options**: Configure script-specific options directly in the overlay.
* **Control**: Start, Stop, and Skip Wait from within the game.

![The in-game interface before starting a script](docs/screenshots/inGameInterface.png) ![The in-game interface while a script runs](docs/screenshots/inGameInterfaceRunning.png)

**Supported aircraft**

| Aircraft | Included Scripts |
|---|---|
| A-4E-C | Cold Start, Hot Start |
| A-10C | Cold Start, Hot Start, Air Start, Shutdown |
| A-10C II | Cold Start, Hot Start, Air Start, Shutdown |
| AH-64D | Cold Start, Hot Start, Shutdown, Load Route, Load Scratchpad |
| AJS37 | Cold Start, Hot Start, Reload Data Cartridge |
| AV-8B N/A | Cold Start, Hot Start, Shutdown |
| C-101CC, C-101EB | Cold Start, Hot Start |
| C-130J-30 | Cold Start, Hot Start, Air Start, Shutdown |
| CH-47F | Cold Start, Hot Start, Shutdown |
| F-4E | Cold Start With Jester, Cold Start No Jester, Auto Start, Hot Start, Air Start |
| F-5E | Cold Start, Hot Start |
| F-15E | Cold Start, Hot Start, Air Start, Shutdown, Load Route, Load Scratchpad |
| F-16C | Cold Start, Hot Start, Air Start, Shutdown, Load Route, Load Scratchpad |
| F-86F | Cold Start, Hot Start, Air Start, Shutdown |
| FA-18C | Cold Start, Hot Start, Air Start, Shutdown, Load Route, Load Scratchpad |
| Ka-50 Black Shark II | Cold Start, Hot Start |
| Ka-50 Black Shark III | Cold Start, Hot Start, Shutdown |
| Mi-8MTV2 | Cold Start, Hot Start, Shutdown |
| Mi-24P | Cold Start, Hot Start, Air Start, Shutdown |
| OH-58D | Cold Start, Hot Start, Shutdown |
| UH-1H | Cold Start, Hot Start, Shutdown |

Only the aircraft listed above are supported by DCSAutoMate 2.0.0, as they're all the ones I've extracted the control definitions for.  To support other aircraft, you will either need to extract the control definitions yourself or wait for a future version of DCSAutoMate that includes them.

**DCSControlPanel**

DCSControlPanel.exe, included in the zip, is a utility for script authors.  It shows the live value of any cockpit control you add to it and lets you operate the control from the desktop.  Its Snapshot Tool records the whole cockpit state so you can find which controls changed after you flip a switch.  **Help > Control Reference** in DCSAutoMate lists every control of every supported aircraft by the name scripts use.

**Settings**

Open the Settings window in the app by clicking the **Tools** menu, then **Settings...**.  Here are the options:

* **Debug** - If checked, you can still run scripts, but no data will be sent to DCS, and DCS doesn't even have to be running.  scriptCockpitState commands will automatically be assumed to meet their conditions (but will still wait for the required duration, if any).  This allows you to test scripts without having to be in the game.
* **Disable Text-to-Speech output** - If checked, no speech will be generated and DCSAutoMate will run silently.
* **In-Game Overlay Hotkey** - The hotkey to toggle the in-game overlay. Defaults to Ctrl+Shift+Z.  Use Ctrl, Alt and Shift as modifiers; left/right-specific modifiers such as LCtrl aren't supported.
* **DCS executable path** - If filled in, DCSAutoMate will use this DCS.exe instead of the one it finds from the registry.  The gray line under the field shows which DCS.exe is actually in use.
* **Find DCS window by window title** - If checked, will make DCSAutoMate try to find the DCS window by searching for the title.  If not checked (default), DCSAutoMate will try to find the DCS window by searching for the Windows process executable, which should be more reliable.  The DCS window is needed in order to send keyboard commands.
* **DCS window title** - If filled in (and "Find DCS window by window title" is checked), DCSAutoMate will look for a window with this value anywhere in its title (case-insensitive) and send the script keyboard commands to the first one it finds.  If left blank, defaults to "Digital Combat Simulator".
* **DCS Saved Games folder path** - If filled in, DCSAutoMate will use this value for the path to the Saved Games folder.  You can use the string `%USERPROFILE%` to represent your personal Users folder.  This path is needed in order to install the DCS-side export script and overlay hook.  If left blank, DCSAutoMate will look for `%USERPROFILE%\Saved Games\DCS`, and if that folder doesn't exist it'll look for `%USERPROFILE%\Saved Games\DCS.openbeta`.  The gray line under the field shows which folder is actually in use, or "Override not found" if the folder you entered doesn't exist.
* **Text-to-Speech** - The voice, speaking rate and volume used for spoken script output.  **Preview Voice** plays a sample with the current choices.
* **Network Communication Ports** - The network ports used for the TCP connection to the DCS export script and for the in-game overlay.  Leave them at defaults unless you know what you're doing.
* **Logging** - Troubleshooting logs for the in-game overlay; leave them off normally.
  * **Log in-game overlay network traffic in DCSAutoMate** - DCSAutoMate records every message it sends to or receives from the in-game overlay in DCSAutoMateLog.txt in the program folder.
  * **Write DCS hook log file** - The DCS-side overlay hook writes a log to Logs\DCSAutoMateHook.log in your DCS Saved Games folder.  The two options under it add to that log, so they're only available when it's checked:
    * **Include debug messages** - Extra detail about what the hook is doing.
    * **Log in-game overlay network traffic in DCS** - The same overlay messages as above, as seen from the DCS side.  Comparing the two logs shows whether a message was lost in between.

**Saved config and settings files**

DCSAutoMate stores its configuration settings in DCSAutoMateConfig.json, and it remembers the last script and options you picked by storing them in DCSAutoMateSettings.json.  You can edit those files manually if you wish, but it's not recommended.  If they get messed up, you can just delete them, and DCSAutoMate will create new ones with default settings.

**Running DCSAutoMate.py as a Python program**

If using DCSAutoMate.exe, no installation or other programs should be needed.  The exe is built with a Python build script (included in the `tools` folder) and includes all necessary dependencies.

If using DCSAutoMate.py, you will need to have [Python 3.13 or greater](https://www.python.org/downloads/windows/) installed, as well as the necessary dependencies, libraries, etc.  The DCSAutoMate.py is normally run in a Python virtual environment (venv), and I recommend you use the DCSAutoMate.bat file to run the app instead, which will set up the virtual environment automatically when it runs.

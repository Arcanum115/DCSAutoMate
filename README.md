# DCSAutoMate

Python scripting engine for DCS World, using DCS-BIOS to drive cockpit controls.

> **Fork notice — [Arcanum115](https://github.com/Arcanum115)**
>
> This fork adds full **Cold Start**, **Shutdown**, and an **Engine Switch Click**
> debug helper for the Anubis Productions **C-130J-30** module. The C-130J
> integration is **working but WIP** — refinements ongoing.
>
> Companion DCS-BIOS additions live at
> [`Arcanum115/dcs-bios`](https://github.com/Arcanum115/dcs-bios). Both repos
> are required for the C-130J scripts to drive the cockpit correctly.
>
> **AI-assisted:** the C-130J Python script and parts of this README were
> developed with assistance from Anthropic's Claude AI. All code was
> hand-verified and tested in DCS by [Arcanum115](https://github.com/Arcanum115)
> before being committed.

---

## Quick start

1. **Download and extract DCSAutoMate.** Grab the latest release zip from this
   fork's [Releases page](https://github.com/Arcanum115/DCSAutoMate/releases)
   and extract it anywhere (e.g. `C:\Tools\DCSAutoMate\`).
2. **Grab the custom DCS-BIOS** from
   [`Arcanum115/dcs-bios`](https://github.com/Arcanum115/dcs-bios) (latest
   release zip).
3. **Install DCS-BIOS** into `C:\Users\<username>\Saved Games\DCS\Scripts\`.
   Full instructions in the
   [dcs-bios README](https://github.com/Arcanum115/dcs-bios#installation).
4. **Edit `Export.lua`** in that same `Scripts\` folder (create it if it
   doesn't exist) and add:
   ```
   dofile(lfs.writedir() .. [[Scripts\DCS-BIOS\BIOS.lua]])
   ```
5. **Launch `DCSAutoMate.exe`**, pick the **Script File** (e.g. `C-130J`),
   pick a **Script** (`Cold Start`, `Shutdown`, etc.), set the **Options**
   (Day/Night, External Power), alt-tab into DCS, press **START**, and
   sit back.

> [!Important]
> Upstream `DCS-Skunkworks/dcs-bios` and the older DCSFlightpanels fork will
> **not** work for the C-130J scripts — only the Arcanum115 fork defines the
> required cockpit controls (FADEC guards, CNI-MU, master caution/warning,
> overhead LCDs, etc.). Upstream aircraft scripts (A-10C, F-16C, F-14, etc.)
> work with either DCS-BIOS distribution.

---

## Features

* **Module / Script selector** — choose the aircraft script file
  (e.g. `C-130J`), then pick a specific script (`Cold Start`, `Shutdown`, …).
* **Per-script options** — each script can declare its own variables (radio
  buttons / dropdowns) shown automatically. C-130J Cold Start exposes
  `Time` (Day / Night) and `External Power` (No / Yes).
* **Start / Stop controls** — large buttons to run or abort the current
  script.
* **Status indicator** — `READY` / `RUNNING` / `STOPPED` badge in the
  top-right corner.
* **DCS-BIOS data stream monitor** — confirms the BIOS export is hooked up
  before you press Start.
* **REALTIME DATA panel** — live cockpit readouts (fuel state, engine RPM,
  APU NG, bleed pressure, etc.).
* **Output console** — scrolling log of every command the script sends
  (DCS-BIOS calls, keyboard inputs, TTS announcements).
* **Light / Dark mode** — toggleable from the Config window.
* **Configurable** — Debug mode (no-op runs), disable text-to-speech, DCS
  window detection by title or executable path, custom Saved Games path.

---

## C-130J support

### Aircraft scripts included

| Module | Scripts | Status |
|-|-|-|
| C-130J-30 (Anubis) | Cold Start (Day/Night, External Power), Shutdown, Test: Engine Switch Click | 🚧 WIP — added in this fork |
| All upstream modules (A-10C, F-16C, F-14, F/A-18C, AH-64D, F-15E, F-4E, M-2000C, Ka-50, Mi-24P, Mi-8MTV2, OH-58D, UH-1H, AJS-37, AV-8B, A-4E, C-101, F-5E, F-86F) | as shipped by [SlipHavoc/DCSAutoMate](https://github.com/SlipHavoc/DCSAutoMate) | ✅ unchanged |

### What the C-130J Cold Start does

Follows the in-game checklist sequence end-to-end:

* **POWER UP** — control boost, oil coolers, electrical pre-stage, ice
  protection, bleed air, pressurisation, fuel management, exterior lighting,
  FADEC / propeller / ATCS, fire / engine start panel, APU, gear, landing
  lights, hydraulics, defensive systems STBY, trim, flaps, parking brake.
* **BATTERY ON** — display backlights, optional EXT POWER, APU start to
  100% N1, APU bleed open to 40 PSI, A/C panel, master caution reset, full
  ECB reset via the CNBP code page, elevator trim to NORM.
* **BEFORE STARTING ENGINES** — aux + suction boost pumps, parking brake
  re-verify.
* **STARTING ENGINES** — bleed valve verify, FADEC RESET cycle, nav lights,
  all four engines start together, 30-second spool-up hold, engines released
  to RUN, generators online.
* **BEFORE TAXI** — propeller controls, radar, prop ice protection,
  alignment wait.
* **TAXI** — taxi and wingtip taxi lights, flaps 50%.
* **BEFORE TAKEOFF** — pitot/NESA heat, landing lights extend, leading edge,
  fuel cross-feeds verified, full CNI-MU defensive setup (MSTR / MWS / IRCM
  power on, OTHER1/2 armed, JMR INTF on, RWR SHOW UNK), defensive systems to
  OPR / AUTO, ADP computer drop, pilot HUD configured, ARC-210 TR+G + SQL,
  standby ADI alignment, ATCS reassert.
* **Night-mode block** (if `Time = Night`) — internal cockpit lights off,
  displays to lowest brightness, both CNI-MU brightness rockers clicked all
  the way down, external lights on, EXT master to NORM.
* **Final** — pilot HUD brightness AUTO, LSGI on all four engines, ATCS
  down, pitot/NESA heat down, FADEC guards closed, prop sync engaged,
  multi-cycle master caution + master warning suppression on pilot and
  copilot, then both CNI-MUs navigated to POWER UP and **AUTONAV +
  MSTR AV ON** engaged on both.

Lamp / display / fire / smoke / brake / trim / lights / pusher BIT tests are
deliberately skipped — they're pilot-action items in the real checklist and
don't affect DCS mission readiness. Runtime is roughly five minutes.

### Requirements

* DCS World 2.9.x
* Anubis Productions **C-130J-30** mod installed
* Matching DCS-BIOS C-130J module from
  [`Arcanum115/dcs-bios`](https://github.com/Arcanum115/dcs-bios) — defines
  `FADEC_GUARD_*`, `PLT_MASTER_CAUTION`, `PLT_CNI_INDX`,
  `CPLT_CNI_BRT_ROCKER`, and the overhead-LCD string outputs (`APU_NG`,
  `BLEED_AIR_PRESSURE`, etc.)

---

## About DCSAutoMate

DCSAutoMate replaces DCS's built-in autostart scripts. After DCS 2.8, those
became subject to the **Pure Scripts** flag on multiplayer servers — modifying
them now breaks IC checks. DCSAutoMate sidesteps this entirely because it
sends commands via DCS-BIOS (a user-editable Saved Games script), which is
not affected by the flag.

DCSAutoMate uses [pydirectinput](https://github.com/learncodebygaming/pydirectinput)
for keyboard inputs and the DCS-BIOS UDP stream for cockpit commands. Beyond
cold/hot starts it can script anything else you'd want to automate —
waypoints, countermeasures programs, radio setup, and so on.

---

## Configuration

Open the config window via **Config → Edit Config**.

| Option | What it does |
|-|-|
| **Debug** | Run scripts without sending data to DCS. `scriptCockpitState` conditions are auto-assumed true (but still wait for `duration`). Useful for testing scripts without launching the game. |
| **Disable Text-to-Speech output** | Silent mode — no spoken narration. |
| **Dark Mode** | Toggle dark UI theme. |
| **Find DCS window by window title** | When checked, locate DCS by matching its window title. Default behaviour (unchecked) locates DCS by executable path, which is more reliable. |
| **DCS window title** | Custom window title to match (used when the option above is checked). Defaults to `Digital Combat Simulator`. |
| **DCS executable path** | Manual override for the DCS exe path (blank = auto-detect from registry). |
| **DCS Saved Games folder path** | Manual override for the Saved Games path. Supports `%USERPROFILE%`. Blank = auto-detect (`%USERPROFILE%\Saved Games\DCS` falling back to `…\DCS.openbeta`). |

DCSAutoMate stores config in `DCSAutoMateConfig.json` and remembers the last
script/options in `DCSAutoMateSettings.json`. Delete either to reset to
defaults.

---

## Running from Python source

`DCSAutoMate.exe` is a fully standalone Windows build — no install required.

To run from source instead, you need Python 3.7+ and:
```
pip install pydirectinput pygetwindow
```

---

## Writing custom scripts

DCSAutoMate scripts live in `DCSAutoMateScripts/<aircraft>.py`. Each script
returns a Python list of dictionaries; each dict is one cockpit command.

<details>
<summary><b>Click to expand the full script-writing reference</b></summary>

All commands must have at least these two keys:

* `'time'`: float — seconds to wait after the previous command before
  running this one. **0.3** is the recommended default for MP server lag.
  Single-player on fast hardware can often use 0.1.
* `'cmd'`: string — either an exact case-sensitive DCS-BIOS control identifier
  (e.g. `'APU_CONTROL_SW'`) or one of the special strings below:
  `scriptKeyboard`, `scriptSpeech`, `scriptCockpitState`, `scriptTimerStart`,
  `scriptTimerEnd`.

### DCS-BIOS commands

Move a cockpit control via DCS-BIOS.

* `'arg'`: string or int — parameter value. Discrete switches/knobs usually
  take `0, 1, …, N`. Continuously-rotating knobs may take `'-3200'` /
  `'+3200'` to rotate one click. Smoothly-rotating knobs with end stops
  usually take `0–65535`.
* `'msg'`: string, optional — message displayed in the output console
  when the command runs.

### scriptKeyboard

Send a keyboard key to DCS, as if you pressed it.

* `'arg'`: string — key name (see
  [pyautogui's key list](https://pyautogui.readthedocs.io/en/latest/keyboard.html#keyboard-keys)).
  Can be a single key (`'a'`) or key + action (`'RCtrl down'`, `'RCtrl up'`).
  Aliases like `'RCtrl'` (instead of `'ctrlright'`) and `'num+'` (instead of
  `'add'`) are accepted.
* `'msg'`: optional message string.

### scriptSpeech

Speak a string via Microsoft TTS.

* `'arg'`: string — text to speak.
* `'msg'`: optional message string.

### scriptCockpitState

Pause the script until a cockpit control reaches a target state. Useful for
waiting on alignments, engine spool-up, canopy positions, etc.

* `'control'`: string — exact case-sensitive `Module/Identifier`, e.g.
  `'FA-18C_hornet/APU_READY_LT'`.
* `'condition'`: string — comparison operator: `=`, `<`, `<=`, `>`, `>=`.
  String values only support `=`.
* `'value'`: string or int — target value to compare against.
* `'duration'`: int, optional — seconds the condition must hold before the
  script continues (defaults to 0).

DCSAutoMate spawns a thread on startup that monitors the DCS-BIOS multicast
stream and builds a complete cockpit state. Initial assembly takes 5–10
seconds — give the runner that time before triggering scripts that
read state near the start.

### scriptTimerStart / scriptTimerEnd

Time long-duration events while continuing to execute other commands.
Useful for fixed-duration alignments.

* `'name'`: string — unique timer name.
* `'duration'`: int — seconds (only used on `scriptTimerStart`).

If enough time has already passed when `scriptTimerEnd` runs, the script
continues immediately.

### Execution model

The runner ticks every 0.01s. When the elapsed time since the previous
command exceeds the current command's `'time'`, it fires the command and
advances. Timing is **relative**, not absolute — matches DCS's own startup
scripts but more flexible.

For a full list of available DCS-BIOS controls, open
`C:\Users\<username>\Saved Games\DCS\Scripts\DCS-BIOS\doc\control-reference.html`
in your browser.

Because scripts are plain Python, you have full language power available —
build sequences with loops, conditionals, helper functions, whatever you need.

</details>

---

## Known limitations

* **Run as Admin** — if DCS runs as Administrator, DCSAutoMate must too,
  otherwise keyboard commands won't reach the game. The runner warns when
  it detects a mismatch.
* **Stay in the cockpit** — keyboard commands only work when DCS has cockpit
  focus. Don't open menus, maps, the rearming screen, or notepads while
  keyboard-using scripts are running. (Regular DCS-BIOS commands are
  unaffected.) The runner warns about scripts with keyboard commands.
* **No time accel / pause awareness** — DCSAutoMate runs on its own clock.
  Time-accelerating or pausing in DCS will desync the script.
* **No state validation** — if you bump a switch mid-script, DCSAutoMate
  won't notice. The bundled scripts mostly don't check for incorrect
  cockpit state, although `scriptCockpitState` lets you add waits where
  needed. Monitor the script as it runs.
* **Command pacing** — 0.3s between commands is reliable in most MP servers.
  Slower computers or laggier networks may need higher values; edit the
  `dt = …` near the top of each script function.
* **DCS window detection** — third-party launchers can confuse the detection.
  If DCSAutoMate can't find DCS, enable "Find DCS window by window title" in
  Config and paste the exact window title.

---

## Credits

* **DCSAutoMate** — [SlipHavoc](https://github.com/SlipHavoc/DCSAutoMate)
  (upstream Python runner and all bundled aircraft scripts except the C-130J)
* **DCS-BIOS** — [DCS-Skunkworks](https://github.com/DCS-Skunkworks/dcs-bios)
  + [`Arcanum115/dcs-bios`](https://github.com/Arcanum115/dcs-bios) fork for
  C-130J support
* **C-130J cockpit module** — Anubis Productions
* **C-130J script + matching DCS-BIOS additions** —
  [Arcanum115](https://github.com/Arcanum115), with AI assistance from
  Anthropic's Claude
* **Libraries** — pydirectinput, pywinauto, pyautogui, pygetwindow
* **Eagle Dynamics** — for DCS World

## License

Distributed under the same license as upstream DCSAutoMate. See
[`LICENSE`](LICENSE) for details.

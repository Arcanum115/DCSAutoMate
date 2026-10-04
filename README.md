# DCSAutoMate

Python scripting engine for DCS World, using DCS-BIOS to drive cockpit controls.

> **Fork notice — [Arcanum115](https://github.com/Arcanum115)**
>
> This fork adds full **Cold Start**, **Shutdown**, an **Engine Switch Click**
> debug helper, and **CARP airdrop automation (beta)** for the Anubis Productions
> **C-130J-30** module. The C-130J integration is **working but WIP** —
> refinements ongoing. See [CARP airdrop automation](#carp-airdrop-automation-beta)
> for what the CARP flow does and what it needs.
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
4. **Copy `DCSAutoMateExport.lua`** (from the DCSAutoMate folder you just
   extracted) into that same `C:\Users\<username>\Saved Games\DCS\Scripts\`
   folder, next to where `Export.lua` lives.
5. **Edit `Export.lua`** in that `Scripts\` folder (create it if it doesn't
   exist) and make sure it contains **both** of these lines, in this order:
   ```
   dofile(lfs.writedir() .. [[Scripts\DCS-BIOS\BIOS.lua]])
   dofile(lfs.writedir()..[[Scripts\DCSAutoMateExport.lua]])
   ```
   **Append** these — don't replace the file, or you'll remove the hooks for
   your other mods and tools. If you already have other export hooks, keep
   them and leave the DCSAutoMate line **last**.
6. **Launch `DCSAutoMate.exe`**, pick the **Script File** (e.g. `C-130J`),
   pick a **Script** (`Cold Start`, `Shutdown`, etc.), set the **Options**
   (Day/Night, External Power), alt-tab into DCS, press **START**, and
   sit back.

> [!IMPORTANT]
> **Both export lines are required.** DCS-BIOS reads and drives the cockpit,
> but it does not export mission weather. `DCSAutoMateExport.lua` is what
> supplies the live **wind and pressure** data, which the CARP flow needs to
> fill in the `CARP INIT 3/5` wind fields. Without the second line the Cold
> Start and Shutdown scripts still run, but CARP cannot auto-fill the winds.
>
> The DCSAutoMate line goes **last** because it chains the previously
> registered export handler — it saves and calls whatever was registered
> before it (DCS-BIOS, TheWay, and so on) before doing its own send, so
> loading it last does not clobber the other hooks.

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
* **Per-script options** — each script can declare its own variables
  (dropdowns) shown automatically. C-130J Cold Start exposes `Time`
  (Day / Night) and `External Power` (No / Yes).
* **Free-entry options** — a script can mark individual options as editable
  (`varEditable`), rendering them as a dropdown you can also **type into**.
  The CARP flow uses this for `Weight lb ea`, so you can pick a listed bundle
  weight or enter any custom one.
* **Mid-list defaults** — a script can declare `varDefaults` to pre-select an
  option that isn't the first in the list, so option lists stay sorted for
  reading while still defaulting to the sensible value.
* **CARP plan-view pane** — selecting a CARP script opens a lookdown diagram
  beside the console showing the run-in and drop zone (turn point, slowdown,
  release point, point of impact, leading/trailing edges, dimension lines and
  wind), with a glossary of the terms underneath. It scales to the pane and
  follows the light/dark theme.
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
| C-130J-30 (Anubis) | **BETA CARP Testing Required** — full CARP airdrop entry, see [below](#carp-airdrop-automation-beta) | 🧪 Beta — added in this fork |
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

## CARP airdrop automation (BETA)

> [!WARNING]
> **This is beta and under active development.** It drives a long sequence of
> CNI-MU keypresses, and a single mistimed press can leave the page part-filled.
> Run it on the ground or in a quiet part of the flight first, watch the output
> console as it goes, and check every CARP page before you trust the solution.
> Known rough edges are listed [below](#known-rough-edges).

### What CARP is

**CARP** stands for **Computed Air Release Point** — the point in space where
cargo has to leave the aircraft so that it lands on the drop zone. It is not the
same as the target: a bundle released directly over the drop zone will overshoot,
because it keeps the aircraft's forward momentum and then drifts under its
parachute. Working out the release point means accounting for ground speed, drop
altitude, the wind through the drop, and how that particular parachute and load
behave.

In the C-130J the crew programs this on the **CNI-MU**, across the `CARP INIT`
pages — the point of impact, the run-in course, drop zone dimensions, load type
and parachute, drop speed, the winds and temperature. The avionics then compute
the release point and drive the green light for the loadmaster.

Entering all of that by hand is a lot of keypresses on a lot of pages. This
script does the entry for you.

### What the script does

Pick **`BETA CARP Testing Required`** as the script for the `C-130J` file. It
runs the whole flow in one pass:

| Phase | Page | What it enters |
| --- | --- | --- |
| 1 | `PAYLOAD (WT+BAL)` | Each bundle as `weight//station` (the double slash marks it as an airdrop), stepping forward from the aftmost station by your chosen spacing. This is a prerequisite for CARP. |
| 2 | `CARP INIT 1/5` | Copies your chosen drop waypoint in as the point of impact, then the drop-zone geometry — leading-to-trailing-edge length, leading-edge-to-PI offset, slowdown and turn-point distances, and the escape leg. |
| 3 | `CARP INIT 2/5` | Load class, fuselage station, element weight and quantity, release system, parachute type and count, and drop speed. |
| 4 | `CARP INIT 3/5` | Winds and temperature. |
| 5 | `CARP INIT 4/5` | Drop altitude and reference, PI and DZ elevations, minimum drop height. |
| 6 | `CARP INIT 4/5` | A **single `EXEC`** at the very end, which commits the whole route. Pages 1–4 are held as a provisional route while `NEXT PAGE` just changes the display, so nothing is lost between pages. |

### What it works out for you

Rather than making you type values you'd have to look up, the script reads them
back out of the aircraft and the mission:

- **Winds** come from the live export. `FROM` enters them meteorologically (the
  direction the wind is coming from, the usual convention), `BLOWS-TO` enters the
  raw DCS direction, and `OFF` leaves the wind fields alone.
- **Altitude temperature** is computed from the surface temperature you give it,
  by lapse rate, for your drop altitude. Surface temperature itself auto-populates
  on the page, so the only thing you supply is the briefed surface temp.
- **PI and DZ elevation** are pulled from the selected waypoint's own height on
  the `ACT LEGS` page, so they are not dropdowns at all.
- **Run-in course** is read from the waypoint's inbound leg, so the CARP run-in
  lines up with the leg you actually planned rather than a heading you type.
- **Drop payload** auto-computes from the element weight and quantity, and the
  parachute count auto-generates.

### What you set

The option list covers the drop itself: which waypoint is the PI, how many
bundles and what each weighs (free-entry, so any weight works), the first
fuselage station and the spacing between bundles, chutes per container, load and
release type, parachute model, drop speed, drop altitude and reference, minimum
drop height, the drop-zone dimensions, and how the winds should be entered.

While a CARP script is selected, the **plan-view pane** opens beside the output
console with a lookdown diagram of the run-in and drop zone — turn point,
slowdown point, computed release point, point of impact, the leading and trailing
edges, the dimension lines and the wind — with a short glossary of each term
underneath.

### Requirements

- Everything in the [C-130J requirements](#requirements) above, plus:
- **Both export lines in `Export.lua`** — see [Quick start](#quick-start) step 5.
  DCS-BIOS does not export mission weather, so without `DCSAutoMateExport.lua`
  the wind fields cannot be auto-filled.
- **The drop waypoint must already be in the flight plan**, with its elevation,
  before you run the script — that is where the PI, the elevations and the run-in
  course are read from. Loading the flight plan with a tool such as TheWay is
  fine; the script only reads what the CNI-MU is showing.
- The matching **`Arcanum115/dcs-bios`** fork, which provides the CNI-MU string
  outputs the script reads back.

### Known rough edges

- **`CARP INIT 2/5` needs unlocking.** If `STAGE` is left at its default the page
  locks and other fields — notably `RELEASE SYS` — will not change. The script
  toggles `STAGE` 1 → 2 → 1 with a deliberate 5-second gap so both presses
  register, ending back on `STAGE 1` for a single-pass drop. The gap is why that
  part of the run looks slow.
- **`RELEASE SYS` cycle order is confirmed for `CDS` only** (`CRS` → `NA` → `TOW`,
  verified in-sim). The `HE` order (`EXTR` / `TOW`) is still unverified.
- **Parachute list positions are assumed** — `G-12D` first, `G-12E` second.
  `G-12E` is untested.
- The flow is built against the DCS C-130J manual and a CARP walkthrough, but
  cockpit mod updates can move CNI fields. If a page fills in wrongly, note which
  page was displayed and what landed in which field, and
  [open an issue](https://github.com/Arcanum115/DCSAutoMate/issues).

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

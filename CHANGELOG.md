# Changelog

All notable changes to the **C-130J-30** automation in this fork are recorded
here. This fork adds Anubis Productions C-130J-30 support on top of SlipHavoc's
DCSAutoMate; entries below are Arcanum115's additions. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/); dates are ISO (YYYY-MM-DD).

Companion module changes live in the `dcs-bios` fork — see its `CHANGELOG.md`.
Most changes are to `DCSAutoMateScripts/C-130J.py` (loaded from disk at runtime,
no rebuild needed); runner changes to `DCSAutoMate.py` are bundled into
`DCSAutoMate.exe` and require `BuildExe.bat` (or running from source).

## [2026-10-03] — Profile list cleanup

- Removed the CARP diagnostic/helper profiles from the dropdown: `CARP Cargo
  Probe`, `Wind Check`, `Export Dump`, `CARP Payload Entry`. Their functions
  remain in `C-130J.py` and can be re-listed in `getScriptData()` if needed.
- Renamed `CARP Test` → `BETA CARP Testing Required`.

## [2026-10-03] — C-130J CARP airdrop automation

Full Computed Air Release Point (CARP) airdrop setup, end to end: weight &
balance, point of impact, drop-zone geometry, load, winds/temperature, and
drop altitude/elevations — typed into the pilot CNI-MU automatically.

### Added — `DCSAutoMateScripts/C-130J.py`
- **`CARP Test` profile** — builds the whole CARP from one Run:
  - **PAYLOAD (WT+BAL)** — types each bundle as `weight//station` (the double
    slash marks an airdrop). First Station is the aftmost (largest) fuselage
    station; the stick steps **forward** by Spacing so every bundle is entered
    for weight & balance (max station 1005).
  - **Point of impact** — downselects the drop waypoint with its **right LSK**
    on ACT LEGS → `MFP>` → MISSIONS → `CARP 1 INIT`, tying the PI to the
    waypoint natively (no scratchpad copy/paste).
  - **Run-in course** — read automatically from the ACT LEGS inbound leg course
    to the drop waypoint, so the run-in points down the WP1→drop bearing.
  - **Drop-zone geometry** — LE-TE, SD DIST, LE-PI, TP DIST, DZ ESC
    (LE-PI entered last with a cleared scratchpad so it reliably lands).
  - **Winds** — ALT W/V and SFC W/V auto-filled from the live LoGet export
    (meteorological FROM direction by default; BLOWS-TO or OFF selectable).
  - **Temperature** — ALT TEMP computed by ISA lapse (~2 °C/1000 ft) from the
    briefed surface temperature; SFC TEMP left to auto-populate.
  - **Elevations** — PI ELEVATION read automatically from the waypoint's ACT
    LEGS height; OBSTR ELEV = PI + 10, DZ ELEV = OBSTR + 10, entered in
    ascending order so the page's PI ≤ OBSTR ≤ DZ rule accepts them.
  - **FUS STA** — the aftmost bundle station (first to leave the ramp).
  - **EXEC after every page** — each CARP INIT page is committed before
    advancing, so nothing is lost on page change.
- **Helper/diagnostic profiles** — `CARP Cargo Probe`, `Wind Check`,
  `Export Dump`, `CARP Payload Entry` (standalone WT+BAL entry).
- **`cni_type()` keyboard helper** — types any value into the CNI scratchpad
  via `PLT_CNI_KBD_*`, working around DCSAutoMate having no input popup; plus
  `lsk()`, `fkey()`, `cycle()` (multi-toggle fields cycled by N presses) and
  `execkey()` helpers.

### Added / Changed — `DCSAutoMate.py` (runner — needs rebuild)
- **Dropdown variable UI** — script variables render as a single `ttk.Combobox`
  per variable instead of a row of radio buttons, so profiles with many
  options (CARP Test has ~20) stay compact.
- **`scriptEcho`** — one-shot read of a control's live value
  (`getControlState(...)[0][2]`), printed and optionally spoken; a reusable
  read primitive that does not gate/wait like `scriptCockpitState`.
- **`scriptExportDump`** — dumps everything the LoGet export is sending, with a
  substring filter, as a survey tool.
- **Build-time snapshot** — `runScript` captures the live LoGet export
  (`config['DAMExportData']`) and key DCS-BIOS CNI strings
  (`config['DCSBIOSData']`: `CARP_LEGS_CRS`, `CARP_LEGS_ELEV`, `CARP_PROBE_A/B`)
  so scripts can read the currently-displayed CNI page (e.g. the ACT LEGS run-in
  course and waypoint elevations) at build time.
- **Telemetry int-cast hardened** — `handleScriptCockpitState` treats an
  empty/non-numeric read as "not met, keep polling" instead of crashing on
  `int('')` before a DCS-BIOS string's first frame arrives.

### Variable ranges (CARP Test / CARP Payload Entry)
- **Weight lb ea** extended to **20,000** (fine steps to 3,000, then 1,000-lb steps).
- **First Station** lists the full fuselage scale **345 → 1005** (20-in steps),
  default 1005 (aftmost).
- **CAS** max raised to **250**.

## [earlier] — C-130J cold start, shutdown & engine-switch test

See `PR_DCSAutoMate.md` for the full write-up.

### Added
- **Cold Start** profile (Day/Night, optional External Power) following the
  in-game checklist: POWER UP → BEFORE START → START (3-4-2-1) → BEFORE TAXI →
  TAXI → BEFORE TAKEOFF, finishing with AUTONAV / MSTR AV ON on both CNI-MUs.
  Includes the pilot AMU/HDD display config (TAWS, DIG MAP, NAV-RADAR,
  GCAS/TAWS) at the end of the start.
- **Shutdown** profile — minimal 5-step sequence (engine start switches → APU →
  external power → battery → generators).
- Two-speed cadence (pre-battery rapid-fire, then normal), telemetry-gated waits
  on `APU_NG` / `BLEED_AIR_PRESSURE`, and master-caution/warning suppression.
- `C-130J_README.md` — end-user documentation.

## Author

Arcanum115

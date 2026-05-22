# Add C-130J-30 cold start, shutdown, and engine-switch test scripts

## Summary

Adds `DCSAutoMateScripts/C-130J.py` for the Anubis Productions C-130J-30 mod,
covering Cold Start (Day/Night, with optional External Power), Shutdown, and a
small engine-switch debug helper.

Cold Start follows the in-game checklist in the order
POWER UP → BEFORE STARTING ENGINES → STARTING ENGINES → BEFORE TAXI →
TAXI → BEFORE TAKEOFF, plus a final block that engages AUTONAV and
MSTR AV ON on both pilot and copilot CNI-MUs.

## Design notes

- **Two-speed cadence**: pre-battery switches rapid-fire at `dt = 0.02`s to
  reach battery-on in seconds, then `dt` is restored to 0.3s for the rest of
  the start so APU spin-up, ECB reset, engine start, and CNI navigation each
  settle between commands.
- **Telemetry-gated waits**: APU and bleed sequences use `scriptCockpitState`
  on `C-130J/APU_NG` (≥100 for 2s) and `C-130J/BLEED_AIR_PRESSURE` (≥40 PSI
  for 2s) rather than fixed sleeps, so the script adapts to slow PCs and cold
  starts in extreme weather. These outputs need the matching DCS-BIOS update
  (see "Companion PR" below).
- **Master caution / warning suppression**: pilot and copilot MC/MW are
  press+release pairs (a press without release leaves the button visually
  stuck down). MC/MW are cleared at every natural pause in the sequence, and
  three spaced cycles at the very end catch any tone re-triggers.
- **Defensive systems via CNI**: walks the CNI-MU to DEF SYS CTRL,
  powers MSTR / MWS / IRCM, arms OTHER1/OTHER2 and JMR INTF on the CMDS
  sub-page, and toggles RWR SHOW UNK on the RWR sub-page. MWS power on is
  what makes the threat audio tones audible on a cold start (they default
  on with a hot start).
- **Engine start switches as relative clicks**: the C-130J engine start
  switches are modelled as relative clicks in the cockpit module. The script
  treats value `1` as "click one detent right" and value `0` as "click one
  detent left" and sequences them accordingly. The `Test: Engine Switch
  Click` script is included so a user can verify this on their install
  before running a full start.
- **Night-mode block**: when `Time = Night` is selected, all internal cockpit
  lights are dropped to zero, display masters to lowest brightness, both
  CNI-MU brightness rockers are clicked DECREASE seven times, all external
  lights are confirmed on, and EXT MASTER goes to NORM. The copilot panel
  backlight has a 0-value wrap quirk (snaps to FULL BRIGHT instead of OFF),
  so it is nudged a fraction above zero to land at essentially off.

## Testing

Tested on DCS 2.9.x with the Anubis C-130J-30 mod over multiple consecutive
cold starts, day and night, with and without External Power. Engines spin up,
ECBs reset, generators come online, defensive systems arm without warnings,
HUD configures, ADI aligns, and the AUTONAV / MSTR AV ON sequence triggers on
both pilot and copilot CNI-MUs at the end. Shutdown brings the aircraft back
to cold and dark.

## Companion PR

This script requires additions to the C-130J DCS-BIOS module — engine /
FADEC / APU / ice / bleed / hydraulic / lighting / A/C / CNBP / defensive /
CNI controls, master caution + master warning, FADEC guards, CPLT CNI
brightness rocker, and the overhead-LCD state outputs (APU_NG, BLEED_AIR_PRESSURE,
etc.). PR opened separately against `DCS-Skunkworks/dcs-bios`.

If the DCS-BIOS PR is not yet merged, users can copy the modified
`C-130J.lua` from this fork into their
`%USERPROFILE%\Saved Games\DCS\Scripts\DCS-BIOS\lib\modules\aircraft_modules\`
to use the script.

## Files

- `DCSAutoMateScripts/C-130J.py` — new
- `C-130J_README.md` — new, end-user documentation (can be merged into the
  main README under an "Aircraft-specific notes" section if preferred)

## Author

Arcanum115

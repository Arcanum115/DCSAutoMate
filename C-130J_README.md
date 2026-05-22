# C-130J Super Hercules

DCSAutoMate script for the Anubis Productions C-130J-30 module.

## Provided sequences

| Script | Vars | Description |
| --- | --- | --- |
| **Cold Start** | `Time` = `Day` \| `Night`<br>`External Power` = `No` \| `Yes` | Full cold start following the in-game checklist. ~5 minute runtime. |
| **Shutdown** | — | Bring the aircraft back to cold and dark, including a transient APU + bleed cycle so generators have load while engines stop. |
| **Test: Engine Switch Click** | `Direction` = `1` (right) \| `0` (left) | Debug helper. Sends a single relative click to all four engine start switches so you can verify the control wiring without running a full start. |

## Cold Start - what it does

Cold Start walks the in-game checklist in order:

1. **POWER UP** — control boost, oil coolers, electrical pre-stage, ice protection,
   bleed air, pressurisation, fuel management, exterior lighting (off), FADEC /
   propeller / ATCS, fire / engine start panel, APU, gear, landing lights,
   hydraulic init, defensive systems STBY, trim, flaps, parking brake.
2. **BATTERY ON** — followed by display backlights to ~85%, optional EXT POWER,
   APU start to 100% N1, APU bleed open to 40 PSI, A/C panel, master caution
   reset, full ECB reset via the CNBP code page, elevator trim to NORM.
3. **BEFORE STARTING ENGINES** — hydraulic aux + suction boost pumps, parking
   brake re-verify.
4. **STARTING ENGINES** — bleed valve verify, FADEC RESET cycle, nav lights and
   strobes to engine-start setting, all four engines start together, 30-second
   spool-up hold, engines released to RUN, generators online.
5. **BEFORE TAXI** — propeller controls, radar, propeller ice protection,
   alignment wait.
6. **TAXI** — taxi and wingtip taxi lights, flaps 50%.
7. **BEFORE TAKEOFF** — pitot / NESA heat, landing lights extend, leading edge,
   fuel cross-feeds verified, full CNI-MU defensive setup (MSTR / MWS / IRCM
   power on, OTHER1/2 armed, JMR INTF on, RWR SHOW UNK), defensive systems to
   OPR / AUTO, ADP computer drop, pilot HUD configured, ARC-210 TR+G + SQL,
   standby ADI alignment, ATCS reassert.
8. **Night-mode block** (if `Time = Night`) — internal cockpit lights off,
   display screens to lowest brightness, CNI-MU brightness clicked all the way
   down on both sides, external lights on, EXT master to NORM.
9. **Final** — pilot HUD brightness AUTO, LSGI on all four engines, ATCS down,
   pitot/NESA heat down, FADEC guards closed, prop sync engaged, multi-cycle
   master caution + master warning suppression on pilot and copilot, then both
   CNI-MUs navigated to POWER UP and AUTONAV + MSTR AV ON engaged on both.

Lamp / display / fire / smoke / brake / trim / lights / pusher BIT tests are
deliberately skipped — they are pilot-action items in the real checklist and
do not affect DCS mission readiness.

## Requirements

- DCSAutoMate (Slip's Python runner)
- DCS-BIOS, with the matching C-130J.lua module from
  [dcs-bios#TBD](https://github.com/DCS-Skunkworks/dcs-bios) (PR adds
  cold-start automation controls)
- Anubis Productions C-130J-30 mod installed

If you are running the script and see any of these symptoms, you most likely
have an older DCS-BIOS C-130J.lua without the cold-start patches:

- `ValueError: invalid literal for int() with base 10: '\x01\x04'` when the
  script polls APU_NG or BLEED_AIR_PRESSURE
- "Switch not found" errors on `FADEC_GUARD_*`, `PLT_MASTER_CAUTION`,
  `PLT_CNI_MC_INDX`, `CPLT_CNI_BRT_ROCKER`, `PLT_CNI_INDX`
- ECB reset hangs at "Wait for ECB page to load"

In all three cases, update C-130J.lua in your DCS-BIOS Saved Games folder to
the version shipped with this script.

## Tested against

- DCS World 2.9.x
- Anubis C-130J-30, manual page references current as of the May 2026 build.

## Credits

- **DCSAutoMate** — [SlipHavoc](https://github.com/SlipHavoc/DCSAutoMate)
- **DCS-BIOS** — [DCS-Skunkworks](https://github.com/DCS-Skunkworks/dcs-bios)
- **C-130J cockpit module** — Anubis Productions
- **Script + DCS-BIOS module additions** — Arcanum115

Feedback, bug reports, and PR contributions welcome.

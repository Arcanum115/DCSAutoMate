# C-130J: add cold-start automation controls and overhead-LCD outputs

## Summary

Extends `lib/modules/aircraft_modules/C-130J.lua` with the controls and string
outputs required to drive the Anubis Productions C-130J-30 from external tools
(joystick boxes, Arduino panels, DCSAutoMate, etc.) through a full cold start
and shutdown.

All command IDs and arg numbers were sourced directly from the C-130J cockpit
module's `command_defs.lua`, `clickabledata.lua`, and `device_init.lua`, so
this PR adds no new behaviour to DCS itself — it only exposes existing
cockpit controls.

## What's added

Roughly grouped by panel:

- **Engine start switches** (4) modelled as relative clicks across MOTOR /
  STOP / RUN / START detents
- **Engine STOP commands** (4) and explicit **FADEC switches + guards** (4 each)
- **APU** switch, stop command, alarm
- **Fire panel**: pull handles and 3-position bottle rotaries for engines 1-4
  and APU
- **Propeller controls** (4), **ATCS** + guard, **prop sync**
- **Bleed air**: APU bleed, L/R wing isolation, divider, 4 × nacelle shutoff
- **Ice protection**: 4 × propeller, engine, wing/empennage, deice, pilot /
  copilot pitot heat, 2 × NESA heat
- **Hydraulic panel**: aux pump, 4 × engine pumps, 2 × suction boost pumps,
  emergency brake select, anti-skid
- **Landing gear + parking brake**
- **Exterior lighting**: master, nav, dim, top/bottom strobe, leading edge,
  landing lights L/R and their motors, taxi, wingtip taxi
- **Air conditioning**: flight station / cargo power and manual
- **CNBP** (Communications / Navigation / Breaker Panel): 0-9, A-Z, soft keys,
  ECB and dedicated function keys — needed for the in-game ECB reset code
  entry
- **Pilot + copilot CNI-MU**: full LSK L1-L6 / R1-R6, INDX, MC INDX, COMM
  TUNE, NAV TUNE, IFF, MSN, DIR INTC, TOLD, CAPS, EXEC, LEGS, MARK,
  PREV/NEXT PAGE, full alphanumeric keyboard, slash, DEL, CLR, BRT rocker,
  status LEDs
- **Pilot + copilot HUD** controls and **REF mode panel** keys
- **Pilot + copilot master caution + master warning** push buttons (arg 80/81
  and 92/93)
- **Overhead LCD string outputs** for APU NG, APU EGT, Bleed Air PSI,
  cabin / cargo air temp, and aux hydraulic pressure, using indication IDs
  33-37 and 43 in line with the existing 23, 24, 38-42 pattern

## Helper added

```lua
local function safe_numeric_lcd(indication_id, length)
```

The cockpit's overhead LCDs display `"---"` (or a similar non-numeric string)
while sensors initialise — notably APU NG during inlet-door opening. Clients
that call `int()` on the raw value crash on those strings. `safe_numeric_lcd`
wraps `parse_overhead_lcd_line` and substitutes a `"0" + spaces` padding string
whenever the value contains a dash or no digits.

The `"0"` is placed first (followed by spaces) rather than last because
DCS-BIOS pushes string updates byte-by-byte; if a client reads the value
before all bytes have arrived, the leading `"0"` guarantees the partial read
still parses as integer 0. The helper is internal to the module and does not
change any existing string-output contracts.

## What this does NOT change

- No removals or signature changes to existing controls
- No changes to other aircraft modules
- No changes to shared libraries

The contribution is contained in a single delimited block at the bottom of
`lib/modules/aircraft_modules/C-130J.lua` (marked `Additional controls /
outputs for full cold-start + shutdown automation` … `End of Arcanum115
contribution block`) plus one master-caution/master-warning definition
inline at the REF mode panel section.

## Testing

Exported JSON and JSONP generate cleanly. All new identifiers were exercised
from a DCSAutoMate cold-start script across multiple consecutive runs in
DCS 2.9.x, day and night, with and without external power. No regressions
observed in existing C-130J controls.

## Files

- `lib/modules/aircraft_modules/C-130J.lua` — modified

## Author

Arcanum115

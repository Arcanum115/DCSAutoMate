# =============================================================================
# C-130J Super Hercules - DCSAutoMate script
# =============================================================================
# Author:   Arcanum115
# Module:   Lockheed Martin C-130J Super Hercules (Mod by Anubis Productions)
# Requires: DCSAutoMate (https://github.com/SlipHavoc/DCSAutoMate)
#           DCS-BIOS C-130J.lua module (matching version)
#
# Provided sequences:
#   - Cold Start  (vars: Time = Day|Night, External Power = No|Yes)
#   - Shutdown
#   - Test: Engine Switch Click   (debug helper, click engine switches L/R)
#
# Cold Start follows the in-game checklist sequence:
#   POWER UP -> BEFORE STARTING ENGINES -> STARTING ENGINES (3,4,2,1)
#                -> BEFORE TAXI -> TAXI -> BEFORE TAKEOFF
# Battery/lamp/display/fire/smoke/brake/trim/lights/pusher BIT tests are
# intentionally omitted - they are pilot-action items in the real checklist
# and do not affect mission readiness in DCS. The script terminates once
# BEFORE TAKEOFF is complete and AUTONAV/MSTR AV ON are engaged on both CNIs.
# =============================================================================


def getScriptData():
	return {
		'scripts': [
			{
				'name': 'Cold Start',
				'function': 'ColdStart',
				'vars': {
					'Time': ['Day', 'Night'],
					'External Power': ['No', 'Yes'],
				},
			},
			{
				'name': 'Shutdown',
				'function': 'Shutdown',
				'vars': {},
			},
			{
				'name': 'BETA CARP Testing Required',
				'function': 'CarpTest',
				# Options lists stay in display order; varDefaults picks the
				# initially-selected entry when it shouldn't be the first one.
				'varDefaults': {'Surface Temp C': '20'},
				'vars': {
					# Full CARP flow: PAYLOAD (WT+BAL) -> PI setup -> CARP INIT 2/5
					# load. No input popup in DCSAutoMate, so values are dropdowns;
					# arbitrary numerics are typed into the CNI scratchpad.
					# --- PI / drop point (TheWay "Waypoint N" -> ident "LL0N") ---
					'CARP Waypoint': ['1', '2', '3', '4', '5', '6', '7', '8', '9'],
					# --- PAYLOAD (WT+BAL) bundles ---
					'Bundles': ['4', '1', '2', '3', '5', '6'],
					'Weight lb ea': ['882', '300', '500', '1000', '1200', '1500',
						'2000', '2200', '2500', '3000', '4000', '5000', '6000',
						'7000', '8000', '9000', '10000', '11000', '12000', '13000',
						'14000', '15000', '16000', '17000', '18000', '19000',
						'20000'],
					# First Station = the AFTMOST (largest) station; the stick steps
					# forward (down) from here. Default 1005 = fully aft (the max).
					'First Station': ['1005', '985', '965', '945', '925', '905',
						'885', '865', '845', '825', '805', '785', '765', '745',
						'725', '705', '685', '665', '645', '625', '605', '585',
						'565', '545', '525', '505', '485', '465', '445', '425',
						'405', '385', '365', '345'],
					'Spacing in': ['60', '48', '72', '90', '120'],
					# --- CARP INIT 2/5 load ---
					'Load': ['CDS', 'HE'],
					# CRS is the standard CDS release (user: always CRS).
					'Release Sys': ['CRS', 'TOW', 'NA', 'EXTR'],
					'Chute': ['G-12D', 'G-12E'],
					'CAS': ['140', '130', '150', '160', '170', '180', '200', '220', '250'],
					# --- CARP INIT 3/5 winds (auto-filled from the live export) ---
					# FROM = meteorological (default); BLOWS-TO = raw DCS direction.
					# OFF = don't touch the wind fields.
					'Winds': ['FROM', 'BLOWS-TO', 'OFF'],
					# --- CARP INIT 3/5 temperature ---
					# Temperature isn't in the export, so give the surface temp from
					# the mission briefing; ALT TEMP is computed by lapse rate for the
					# drop altitude. SFC TEMP auto-populates, so we leave it.
					'Surface Temp C': ['-5', '0', '5', '10', '15', '20', '25', '30'],
					'Drop Alt ft': ['1000', '500', '800', '1250', '1500', '2000',
						'2500', '5000', '10000'],
					# --- CARP INIT 1/5 geometry (drop-zone dimensions) ---
					# Defaults from the CARP walkthrough. OFF skips geometry entry.
					'Geometry': ['ON', 'OFF'],
					'LE-TE yd': ['1000', '500', '750', '1250', '1500', '2000'],
					'LE-PI yd': ['100', '0', '50', '200', '300', '500'],
					'SD Dist NM': ['6', '4', '5', '8', '10'],
					'TP Dist NM': ['10', '6', '8', '12', '15'],
					'DZ ESC NM': ['0.5', '1', '1.5', '2'],
					# --- CARP INIT 4/5 drop altitude + elevations ---
					# Drop Alt uses the 'Drop Alt ft' var above. QNH = MSL ref.
					'Drop Alt Ref': ['QNH', 'PA'],
					# PI ELEV and DZ ELEV are NOT dropdowns: both are pulled
					# automatically from the selected waypoint's ACT LEGS "A"
					# height (set by TheWay), PI == DZ.
					'Min Drop Ht ft': ['600', '400', '500', '800', '1000'],
				},
			},
			# NOTE: the CARP diagnostic/helper profiles (CARP Cargo Probe,
			# Wind Check, Export Dump, CARP Payload Entry) were removed from
			# this dropdown list 2026-10-03; their functions (CarpProbe,
			# WindCheck, ExportDump, CarpPayload) remain below and can be
			# re-listed here if needed.
		],
	}


def getInfo():
	return ('C-130J Cold Start follows the in-game checklist sequence:\n'
			'POWER UP -> BEFORE START -> START (3-4-2-1) -> BEFORE TAXI -> TAXI -> BEFORE TAKEOFF.\n'
			'Pre-battery switches are rapid-fired; everything from battery-on runs at normal cadence.\n'
			'Tests skipped. Stops when ready for takeoff. Runtime ~5 min.')


def int16(mult=1):
	# DCS-BIOS 16-bit potentiometers / multi-pos switches take 0..65535.
	# int16(0.5) -> mid-travel, int16(1.0) -> full deflection.
	return int(mult * 65535)


###############################################################################
# COLD START
# ---------------------------------------------------------------------------
# Follows the in-game checklist order. Battery is the only "slow" pivot; all
# pre-battery switches are rapid-fired at dt=0.02 so the cockpit comes alive
# almost instantly. Once battery is energised, dt is restored to 0.3 so the
# avionics, APU, and engine sequences can settle between commands.
###############################################################################
def ColdStart(config, vars):
	seq = []
	seqTime = 0
	# Pre-batt switches rapid-fire at 0.02s spacing; reset to 0.3s right before
	# BATTERY - ON so the rest of the sequence keeps its normal cadence.
	dt = 0.02

	def pushSeqCmd(dt, cmd, *args, **kwargs):
		nonlocal seq, seqTime
		if len(args):
			seq.append({
				'time': round(dt, 2),
				'cmd': cmd,
				'arg': args[0],
				'msg': args[1] if len(args) > 1 else '',
			})
		else:
			step = {
				'time': round(dt, 2),
				'cmd': cmd,
			}
			for key in kwargs:
				step[key] = kwargs[key]
			seq.append(step)

	def mc_mw_silence(num_cycles, label='silence', interval=0.02):
		"""
		Emit `num_cycles` instant press+release pairs on Pilot Master Caution
		and Pilot Master Warning, back-to-back with no inter-cycle delay.

		Each cycle is (all timings are instant 0.02s rapid-fire):
		  +interval s : MC press (value 1)   — instant after previous cycle
		  +0.02 s     : MC release (value 0)
		  +0.02 s     : MW press (value 1)
		  +0.02 s     : MW release (value 0)

		One full cycle takes ~0.08s, so `num_cycles=12` fires in ~1 second.
		Called at every cold-start phase boundary so the alarms get hammered
		whenever the script reaches a transition point.
		"""
		for i in range(1, num_cycles + 1):
			pushSeqCmd(interval, 'PLT_MASTER_CAUTION', 1, f'MC {label} cycle {i}/{num_cycles}')
			pushSeqCmd(0.02,     'PLT_MASTER_CAUTION', 0)
			pushSeqCmd(0.02,     'PLT_MASTER_WARNING', 1, f'MW {label} cycle {i}/{num_cycles}')
			pushSeqCmd(0.02,     'PLT_MASTER_WARNING', 0)

	pushSeqCmd(0, '', '', "C-130J Cold Start (in-game checklist order)")
	pushSeqCmd(dt, 'scriptSpeech', 'Starting checklist.')

	# ===========================================================================
	# CHECKLIST: POWER UP
	# ===========================================================================

	# CONTROL BOOST switches - ON/guarded
	for cvr, sw in [
		('CTRL_BOOST_ELEVATOR_BOOST_GUARD','CTRL_BOOST_ELEVATOR_BOOST'),
		('CTRL_BOOST_ELEVATOR_UTIL_GUARD','CTRL_BOOST_ELEVATOR_UTIL'),
		('CTRL_BOOST_RUDDER_BOOST_GUARD','CTRL_BOOST_RUDDER_BOOST'),
		('CTRL_BOOST_RUDDER_UTIL_GUARD','CTRL_BOOST_RUDDER_UTIL'),
		('CTRL_BOOST_AILERON_BOOST_GUARD','CTRL_BOOST_AILERON_BOOST'),
		('CTRL_BOOST_AILERON_UTIL_GUARD','CTRL_BOOST_AILERON_UTIL'),
	]:
		pushSeqCmd(dt, cvr, 1)
		pushSeqCmd(dt, sw, 1)
		pushSeqCmd(dt, cvr, 0)

	# OIL COOLER FLAPS switches - AUTOMATIC
	# Oil cooler flaps values: 0=FIXED, 1=AUTO, 2=OPEN, 3=CLOSE
	pushSeqCmd(dt, 'OIL_COOLER_FLAPS_1', 1, 'Oil cooler 1 - AUTO')
	pushSeqCmd(dt, 'OIL_COOLER_FLAPS_2', 1, 'Oil cooler 2 - AUTO')
	pushSeqCmd(dt, 'OIL_COOLER_FLAPS_3', 1, 'Oil cooler 3 - AUTO')
	pushSeqCmd(dt, 'OIL_COOLER_FLAPS_4', 1, 'Oil cooler 4 - AUTO')

	# ELECTRICAL panel - pre-stage for power-on
	# Generators set ON and EXT PWR/APU selector set to APU BEFORE battery on,
	# so the buses come live immediately when battery is energised.
	pushSeqCmd(dt, 'ELECTRICAL_GENERATOR_1', 1, 'Gen 1 - ON (pre-staged)')
	pushSeqCmd(dt, 'ELECTRICAL_GENERATOR_2', 1, 'Gen 2 - ON (pre-staged)')
	pushSeqCmd(dt, 'ELECTRICAL_GENERATOR_3', 1, 'Gen 3 - ON (pre-staged)')
	pushSeqCmd(dt, 'ELECTRICAL_GENERATOR_4', 1, 'Gen 4 - ON (pre-staged)')
	pushSeqCmd(dt, 'ELECTRICAL_BATTERY', 0, 'Battery - OFF (about to turn on)')
	pushSeqCmd(dt, 'ELECTRICAL_EXT_POWER_APU', 2, 'EXT PWR/APU - APU (pre-staged)')

	# ICE PROTECTION panel RESET
	pushSeqCmd(dt, 'ICE_PROP_1', 0, 'Prop ice 1 - OFF')
	pushSeqCmd(dt, 'ICE_PROP_2', 0, 'Prop ice 2 - OFF')
	pushSeqCmd(dt, 'ICE_PROP_3', 0, 'Prop ice 3 - OFF')
	pushSeqCmd(dt, 'ICE_PROP_4', 0, 'Prop ice 4 - OFF')
	pushSeqCmd(dt, 'ICE_ENGINE', 0, 'Engine ice - OFF')
	pushSeqCmd(dt, 'ICE_WING', 0, 'Wing/Emp ice - OFF')
	pushSeqCmd(dt, 'ICE_DEICE', 1, 'Anti-Ice/De-Ice - DE-ICE')
	pushSeqCmd(dt, 'ICE_PITOT_P', 0, 'Pilot pitot - OFF')
	pushSeqCmd(dt, 'ICE_PITOT_CP', 0, 'Copilot pitot - OFF')
	pushSeqCmd(dt, 'ICE_NESA_CTR', 0, 'NESA center - OFF')
	pushSeqCmd(dt, 'ICE_NESA_SIDE', 0, 'NESA side - OFF')

	# BLEED AIR panel - AUTO
	pushSeqCmd(dt, 'BLEED_ISO_L', 1, 'L ISO - AUTO')
	pushSeqCmd(dt, 'BLEED_ISO_R', 1, 'R ISO - AUTO')
	pushSeqCmd(dt, 'BLEED_DIVIDER', 1, 'Divider - AUTO')
	pushSeqCmd(dt, 'BLEED_NAC_1', 1, 'Nacelle 1 - AUTO')
	pushSeqCmd(dt, 'BLEED_NAC_2', 1, 'Nacelle 2 - AUTO')
	pushSeqCmd(dt, 'BLEED_NAC_3', 1, 'Nacelle 3 - AUTO')
	pushSeqCmd(dt, 'BLEED_NAC_4', 1, 'Nacelle 4 - AUTO')

	# PRESSURIZATION panel
	pushSeqCmd(dt, 'PRESS_RATE_CONTROL_KNOB', int16(1.0), 'Auto rate - full RIGHT')
	pushSeqCmd(dt, 'PRESS_EMER_DUMP', 0, 'Emer depress - NORM')
	pushSeqCmd(dt, 'PRESS_EMER_DUMP_GUARD', 0, 'Emer depress guard - down')
	pushSeqCmd(dt, 'PRESS_MODE', 2, 'Pressurization mode - AUTO')

	# FUEL MANAGEMENT panel
	pushSeqCmd(dt, 'FUEL_DUMP_L', 0)
	pushSeqCmd(dt, 'FUEL_DUMP_L_GUARD', 0, 'L Dump guard - down')
	pushSeqCmd(dt, 'FUEL_DUMP_R', 0)
	pushSeqCmd(dt, 'FUEL_DUMP_R_GUARD', 0, 'R Dump guard - down')
	pushSeqCmd(dt, 'FUEL_TANK_SELECTOR', 0, 'Tank select - OFF')
	pushSeqCmd(dt, 'FUEL_SPR_VALVE', 1, 'SPR - CLOSED')
	pushSeqCmd(dt, 'FUEL_XFEED_SHIP', 0, 'Cross-ship - CLOSED')
	pushSeqCmd(dt, 'FUEL_XFEED_ENG_1', 0)
	pushSeqCmd(dt, 'FUEL_XFEED_ENG_2', 0)
	pushSeqCmd(dt, 'FUEL_XFEED_ENG_3', 0)
	pushSeqCmd(dt, 'FUEL_XFEED_ENG_4', 0)
	for tank in ('MAIN_1','MAIN_2','MAIN_3','MAIN_4','AUX_L','AUX_R','EXT_L','EXT_R'):
		pushSeqCmd(dt, f'FUEL_XFER_{tank}', 1)

	# EXTERIOR LIGHTING panel - all OFF initially
	pushSeqCmd(dt, 'EXT_MASTER', 0, 'Exterior master - NORM (down)')
	pushSeqCmd(dt, 'EXT_NAV', 1, 'Nav - OFF')
	pushSeqCmd(dt, 'EXT_DIM', 1, 'Nav BRIGHT')
	pushSeqCmd(dt, 'EXT_STROBE_TOP', 1, 'Top strobe - OFF')
	pushSeqCmd(dt, 'EXT_STROBE_BTM', 1, 'Bottom strobe - OFF')
	pushSeqCmd(dt, 'EXT_LEDGE', 0, 'Leading edge - OFF')

	# FADEC/PROPELLER CONTROL panel
	pushSeqCmd(dt, 'FADEC_1', 1, 'FADEC 1 - NORM')
	pushSeqCmd(dt, 'FADEC_2', 1)
	pushSeqCmd(dt, 'FADEC_3', 1)
	pushSeqCmd(dt, 'FADEC_4', 1)
	pushSeqCmd(dt, 'PROP_CTRL_1', 1, 'Prop ctrl 1 - NORMAL')
	pushSeqCmd(dt, 'PROP_CTRL_2', 1)
	pushSeqCmd(dt, 'PROP_CTRL_3', 1)
	pushSeqCmd(dt, 'PROP_CTRL_4', 1)
	pushSeqCmd(dt, 'ATCS_GUARD', 1)
	pushSeqCmd(dt, 'ATCS', 1, 'ATCS - ON')
	pushSeqCmd(dt, 'ATCS_GUARD', 0)
	# NOTE: PROP_SYNC is intentionally NOT engaged here. The system rejects
	# engagement attempts when engines aren't running at a stable RPM, so
	# the engagement is deferred to the absolute end of the script (after
	# AUTONAV / MSTR AV ON) when all four engines are fully spooled and
	# stable.

	# FIRE/ENGINE START panel - engines initial position
	# Engine start switches behave as RELATIVE CLICKS, not absolute positions:
	#   value 1 = click right one detent (MOTOR -> STOP -> RUN -> START)
	#   value 0 = click left one detent
	# A single right-click here lands the engines in a known initial detent
	# (STOP / centre) regardless of where the mission ended them.
	pushSeqCmd(dt, 'ENG_1_START_SWITCH', 1, 'Engine 1 - click right (initial)')
	pushSeqCmd(dt, 'ENG_2_START_SWITCH', 1)
	pushSeqCmd(dt, 'ENG_3_START_SWITCH', 1)
	pushSeqCmd(dt, 'ENG_4_START_SWITCH', 1)

	# APU panel
	pushSeqCmd(dt, 'APU_SWITCH', 0, 'APU - STOP (initial)')

	# Landing gear lever DOWN
	pushSeqCmd(dt, 'GEAR_LEVER', 1, 'Gear lever - DOWN')

	# LANDING LIGHTS panel
	pushSeqCmd(dt, 'LDG_MOTOR_L', 1, 'L motor - HOLD')
	pushSeqCmd(dt, 'LDG_MOTOR_R', 1, 'R motor - HOLD')
	pushSeqCmd(dt, 'LDG_LIGHT_L', 0, 'L landing - OFF')
	pushSeqCmd(dt, 'LDG_LIGHT_R', 0, 'R landing - OFF')
	pushSeqCmd(dt, 'TAXI_LIGHT', 0, 'Taxi - OFF')
	pushSeqCmd(dt, 'WINGTIP_TAXI', 0, 'Wingtip taxi - OFF')

	# HYDRAULIC panel initial
	pushSeqCmd(dt, 'ANTI_SKID', 1, 'Anti-skid - ON')
	pushSeqCmd(dt, 'HYD_AUX_PUMP', 0, 'Aux pump - OFF (initial)')

	# PILOT LIGHTING panel MASTER - NORM
	pushSeqCmd(dt, 'PLT_CC_LIGHTING_MASTER_SWITCH', 1, 'Master lighting - NORM')

	# RADAR MASTER - OFF
	pushSeqCmd(dt, 'RCP_MASTER_POWER', 0, 'Radar - OFF (initial)')

	# DEFENSIVE SYSTEMS panel - initial STBY positions; CMS jettison guard closed
	pushSeqCmd(dt, 'DSP_DEFENSIVE_MASTER_SWITCH', 0, 'Defensive master - STBY')
	pushSeqCmd(dt, 'DSP_ECM_MASTER', 0, 'ECM - STBY')
	pushSeqCmd(dt, 'DSP_IRCM_MASTER', 0, 'IRCM - STBY')
	pushSeqCmd(dt, 'DSP_CMDS_MODE', 0, 'CMDS - STBY')
	pushSeqCmd(dt, 'DSP_CMS_JETTISON_SWITCH', 0, 'CMS Jettison - OFF')
	pushSeqCmd(dt, 'DSP_CMS_JETTISON_GUARD', 0, 'CMS Jettison guard - down')

	# Elevator trim power OFF (initial)
	pushSeqCmd(dt, 'TRIM_ELEV_TAB_PWR', 0, 'Elev trim power - OFF')

	# Flaps UP
	pushSeqCmd(dt, 'CC_FLAP_LEVER', 0, 'Flaps - UP')

	# Parking brake SET
	pushSeqCmd(dt, 'PARKING_BRAKE', 1, 'Parking brake - SET')

	# --- LAST STEP BEFORE BATT ON: confirm all control boost guards are DOWN ---
	# Belt-and-suspenders: even though the guard-up/switch-on/guard-down loop
	# above closed them, force each guard explicitly to 0 right before power on.
	for guard in (
		'CTRL_BOOST_ELEVATOR_BOOST_GUARD',
		'CTRL_BOOST_ELEVATOR_UTIL_GUARD',
		'CTRL_BOOST_RUDDER_BOOST_GUARD',
		'CTRL_BOOST_RUDDER_UTIL_GUARD',
		'CTRL_BOOST_AILERON_BOOST_GUARD',
		'CTRL_BOOST_AILERON_UTIL_GUARD',
	):
		pushSeqCmd(dt, guard, 0, f'{guard} - DOWN')

	# --- Airplane Power Application ---
	# Restore normal cadence for the rest of the cold start regardless of mode.
	dt = 0.3
	pushSeqCmd(dt, '', '', 'announcement removed')
	pushSeqCmd(dt, 'ELECTRICAL_BATTERY', 1, 'BATTERY - ON')
	pushSeqCmd(2.0, '', '', 'announcement removed')

	pushSeqCmd(dt, 'PLT_CC_LIGHTING_MASTER_DISPLAY_BRIGHTNESS',  int16(0.85))
	pushSeqCmd(dt, 'CPLT_CC_LIGHTING_MASTER_DISPLAY_BRIGHTNESS', int16(0.85))

	# --- External Power (optional, electrical only) ---
	# EXT PWR provides electrical supply. APU is still needed for bleed air
	# during engine start, so we always run the APU sequence below regardless.
	if vars.get('External Power') == 'Yes':
		pushSeqCmd(dt, 'ELECTRICAL_EXT_POWER_APU', 0, 'EXT PWR/APU - EXT PWR')
		pushSeqCmd(2.0, '', '', 'announcement removed')

	# --- APU Start (always run: APU bleed air is required for engine start) ---
	pushSeqCmd(dt, '', '', 'announcement removed')
	# APU control switch is spring-loaded out of START. Procedure:
	#   1) Drive switch to START (value 2)
	#   2) Hold ~2s for the start sequence to engage
	#   3) Release to RUN (value 1)
	#   4) Silence the master caution alarm every 10 seconds while the APU
	#      spools up (the alarm re-triggers on each ACAWS condition during
	#      APU start)
	#   5) Final telemetry check that APU_NG actually reached 100%
	pushSeqCmd(dt, 'APU_SWITCH', 2, 'APU switch - START')
	pushSeqCmd(2.0, 'APU_SWITCH', 1, 'APU switch - RUN (release from spring)')

	# Periodic MC + MW silence while APU spools (~60s coverage).
	mc_mw_silence(12, label='APU spool')

	# Settle delay before the FIRST telemetry read of the script. DCS-BIOS
	# streams string outputs (APU_NG etc.) byte-by-byte on a slower loop than
	# the numeric outputs, and the client's buffer for a string is EMPTY until
	# its first frame arrives. Polling APU_NG before that first frame makes the
	# runner do int('') and crash (same failure class as the '\x01\x04' garbage
	# read the README documents). This fixed wait guarantees at least one APU_NG
	# frame has landed; once populated the string never reads empty again.
	# (Cheap insurance — the APU needs this long to spool anyway.)
	pushSeqCmd(5.0, '', '', 'Allow APU_NG telemetry to populate before first poll')

	# Final guard — if APU is already at 100% (which it should be after the
	# 60s of MC silencing above), this passes immediately. If for some reason
	# the APU spool is slow, this will wait until it gets there.
	pushSeqCmd(dt, 'scriptCockpitState',
		control='C-130J/APU_NG', value=100, condition='>=', duration=2)
	pushSeqCmd(dt, '', '', 'announcement removed')

	# MC clear after APU online
	pushSeqCmd(dt, 'PLT_MASTER_CAUTION', 1, 'MC clear after APU')
	pushSeqCmd(0.5, 'PLT_MASTER_CAUTION', 0)
	pushSeqCmd(0.3, 'PLT_MASTER_WARNING', 1, 'MW clear after APU')
	pushSeqCmd(0.3, 'PLT_MASTER_WARNING', 0)

	# Open APU bleed air
	pushSeqCmd(dt, 'BLEED_APU', 1, 'APU bleed air - OPEN')
	pushSeqCmd(dt, '', '', 'announcement removed')

	# Wait for bleed pressure to reach 30 PSI
	pushSeqCmd(dt, 'scriptCockpitState',
		control='C-130J/BLEED_AIR_PRESSURE', value=30, condition='>=', duration=2)
	pushSeqCmd(dt, '', '', 'announcement removed')

	# APU switch - click left one detent (value 0) to settle in RUN.
	pushSeqCmd(dt, 'APU_SWITCH', 0, 'APU switch - click left to RUN')

	# MC + MW silence cycles after bleed stable (~15s coverage through
	# A/C panel + ECB prep).
	mc_mw_silence(3, label='after bleed')

	# --- AIR COND panel - Set (as required) ---
	pushSeqCmd(dt, 'AC_FLT_PWR', 1, 'Flt Station A/C - ON')
	pushSeqCmd(dt, 'AC_CARGO_PWR', 1, 'Cargo A/C - ON')

	# --- Master Caution reset + ECB reset (full procedure from in-game checklist) ---
	# MUST complete before engines can be started.
	pushSeqCmd(dt, '', '', 'announcement removed')
	pushSeqCmd(dt, 'PLT_MASTER_CAUTION', 1)
	pushSeqCmd(0.5, 'PLT_MASTER_CAUTION', 0)
	pushSeqCmd(0.3, 'PLT_MASTER_WARNING', 1, 'MW clear (initial)')
	pushSeqCmd(0.3, 'PLT_MASTER_WARNING', 0)

	# CNBP setup before ECB - send display to HDD2, press LSK L1
	pushSeqCmd(dt, 'CNBP_NUM_2', 1, 'CNBP 2 key - prep HDD2')
	pushSeqCmd(0.5, 'CNBP_NUM_2', 0)
	pushSeqCmd(dt, 'CNBP_BTN_L1', 1, 'CNBP LSK L1 - select')
	pushSeqCmd(0.5, 'CNBP_BTN_L1', 0)
	pushSeqCmd(1.0, '', '', 'Pause before ECB sequence')

	pushSeqCmd(dt, 'scriptSpeech', 'Resetting electronic circuit breakers.')
	# Step 1: Open ECB page on CNBP. HDD2 was already selected by the prep step
	# (CNBP_NUM_2 + CNBP_BTN_L1) above; do NOT press NUM 2 again here or the
	# "2" gets injected into the digit SELECT field.
	pushSeqCmd(dt, 'CNBP_ECB', 1, 'CNBP ECB key')
	pushSeqCmd(0.5, 'CNBP_ECB', 0)
	pushSeqCmd(2.0, '', '', 'Wait for ECB page to load')

	# Step 2: Enter the 24-digit reset code: 481 482 483 902 108 109 609 613
	# (codes per in-game ECB BY SYSTEM page: 481/482/483/902 prop aux pumps,
	#  108/109/609/613 fire handle oil)
	ecb_code = '481482483902108109609613'
	for digit in ecb_code:
		pushSeqCmd(0.1, f'CNBP_NUM_{digit}', 1, f'CNBP digit {digit}')
		pushSeqCmd(0.1, f'CNBP_NUM_{digit}', 0)

	# Step 3: Press LSK R1 to initiate reset, then again to confirm
	pushSeqCmd(0.2, '', '', 'Pause before reset')
	pushSeqCmd(dt, 'CNBP_BTN_R1', 1, 'CNBP LSK R1 - Reset')
	pushSeqCmd(0.2, 'CNBP_BTN_R1', 0)
	pushSeqCmd(0.5, '', '', 'Wait for confirm prompt')
	pushSeqCmd(dt, 'CNBP_BTN_R1', 1, 'CNBP LSK R1 - Confirm')
	pushSeqCmd(0.2, 'CNBP_BTN_R1', 0)
	pushSeqCmd(dt, '', '', 'announcement removed')
	# MC + MW silence cycles after ECB reset (~15s coverage through
	# alignment timer + BEFORE STARTING ENGINES).
	mc_mw_silence(3, label='after ECB')

	# --- Elevator trim power to NORM (after power application) ---
	pushSeqCmd(dt, 'TRIM_ELEV_TAB_PWR', 2, 'Elev trim power - NORM')

	# CNI-MU initialization - wait for alignment to start
	pushSeqCmd(dt, '', '', 'announcement removed')
	pushSeqCmd(dt, 'scriptTimerStart', name='align', duration=5)


	# ===========================================================================
	# CHECKLIST: BEFORE STARTING ENGINES
	# ===========================================================================

	# HYDRAULIC panel - Set
	# AUX_PUMP is a regular toggle - just set ON
	pushSeqCmd(dt, 'HYD_AUX_PUMP', 1, 'Aux pump - ON')
	pushSeqCmd(2.0, '', '', 'Aux pressure check')

	# Suction boost pumps - single press toggles ON.  Do NOT send value 0 after,
	# that would toggle it back OFF.
	# Engine-driven pumps (HYD_ENG_PUMP_1..4) are pressed AFTER engine start.
	pushSeqCmd(dt, 'HYD_SUCT_BOOST_UTIL',  1, 'Suction boost util - press to ON')
	pushSeqCmd(dt, 'HYD_SUCT_BOOST_BOOST', 1, 'Suction boost boost - press to ON')

	# Parking brake re-verify (pressure now available)
	pushSeqCmd(dt, 'PARKING_BRAKE', 1, 'Parking brake - SET (pressure check)')


	# ===========================================================================
	# CHECKLIST: STARTING ENGINES
	# Real-world checklist starts in the order 3, 4, 2, 1 for ground-crew clearance,
	# but this script issues the start clicks together since DCS does not enforce
	# the sequencing rule. All four spool up in parallel for a faster start.
	# ===========================================================================
	pushSeqCmd(dt, '', '', 'announcement removed')

	# Verify bleed air valves at AUTO (middle) immediately before engine start
	# (re-asserted in case anything moved them during APU bring-up)
	pushSeqCmd(dt, 'BLEED_ISO_L', 1, 'Left ISO - AUTO')
	pushSeqCmd(dt, 'BLEED_NAC_1', 1, 'Nacelle 1 - AUTO')
	pushSeqCmd(dt, 'BLEED_NAC_2', 1, 'Nacelle 2 - AUTO')
	pushSeqCmd(dt, 'BLEED_DIVIDER', 1, 'Divider - AUTO')
	pushSeqCmd(dt, 'BLEED_ISO_R', 1, 'Right ISO - AUTO')
	pushSeqCmd(dt, 'BLEED_NAC_3', 1, 'Nacelle 3 - AUTO')
	pushSeqCmd(dt, 'BLEED_NAC_4', 1, 'Nacelle 4 - AUTO')

	# FADEC switches - RESET (cycle each to RESET position, then back to NORM)
	# 3-pos spring-loaded: 0=ALT, 1=NORM (center), 2=RESET
	for n in [1, 2, 3, 4]:
		pushSeqCmd(dt, f'FADEC_{n}', 2, f'FADEC {n} - RESET')
		pushSeqCmd(0.4, f'FADEC_{n}', 1, f'FADEC {n} - NORM')

	# Exterior lighting for engine start
	pushSeqCmd(dt, 'EXT_NAV', 0, 'Nav lights - STEADY (down)')
	pushSeqCmd(dt, 'EXT_DIM', 1)
	pushSeqCmd(dt, 'EXT_STROBE_TOP', 0, 'Top strobe - RED')
	pushSeqCmd(dt, 'EXT_STROBE_BTM', 0, 'Bottom strobe - RED')

	# AIR COND CARGO COMPT PWR - OFF during engine start (FCV will close anyway)
	pushSeqCmd(dt, 'AC_CARGO_PWR', 0, 'Cargo A/C - OFF (during start)')

	# --- Engine start ---
	# ENG_n_START_SWITCH values are RELATIVE CLICK directions:
	#   value 1 = click switch one detent to the RIGHT
	#   value 0 = click switch one detent to the LEFT
	pushSeqCmd(dt, 'scriptSpeech', 'Starting all engines.')

	# Click all 4 engines right once (moves into START position)
	pushSeqCmd(dt, 'ENG_1_START_SWITCH', 1, 'Engine 1 - click right')
	pushSeqCmd(dt, 'ENG_2_START_SWITCH', 1, 'Engine 2 - click right')
	pushSeqCmd(dt, 'ENG_3_START_SWITCH', 1, 'Engine 3 - click right')
	pushSeqCmd(dt, 'ENG_4_START_SWITCH', 1, 'Engine 4 - click right')

	pushSeqCmd(dt, '', '', 'announcement removed')

	# MC + MW silence cycles for the entire 30s hold (~30s coverage).
	mc_mw_silence(6, label='engine spool')

	# After 30s at START, click each engine one detent left back to RUN
	pushSeqCmd(dt, '', '', 'announcement removed')
	pushSeqCmd(dt, 'ENG_1_START_SWITCH', 0, 'Engine 1 - click left to RUN')
	pushSeqCmd(dt, 'ENG_2_START_SWITCH', 0, 'Engine 2 - click left to RUN')
	pushSeqCmd(dt, 'ENG_3_START_SWITCH', 0, 'Engine 3 - click left to RUN')
	pushSeqCmd(dt, 'ENG_4_START_SWITCH', 0, 'Engine 4 - click left to RUN')

	# MC + MW silence cycles after engines at RUN (~15s coverage).
	mc_mw_silence(3, label='engines at RUN')

	# --- Post-engine-start: CNBP LSK L1 ---
	pushSeqCmd(dt, '', '', 'announcement removed')

	# CNBP LSK L1 press - single press only
	pushSeqCmd(dt, 'CNBP_BTN_L1', 1, 'CNBP LSK L1 - press')

	# NOTE: Engine hydraulic utility/booster pumps are pressed AFTER CMDS setup
	# (moved to BEFORE TAKEOFF phase per startup procedure).
	# Emergency parking brake is left for the pilot to set when ready.

	# AIR COND restore (cargo)
	pushSeqCmd(dt, 'AC_CARGO_PWR', 1, 'Cargo A/C - ON')


	# --- Generators online ---
	# Generators were pre-staged to ON earlier - they come online as engines stabilise.
	# APU stays RUNNING; the pilot decides when to shut it down.
	pushSeqCmd(dt, '', '', 'announcement removed')
	pushSeqCmd(dt, 'ELECTRICAL_GENERATOR_1', 1, 'Gen 1 - ON')
	pushSeqCmd(dt, 'ELECTRICAL_GENERATOR_2', 1)
	pushSeqCmd(dt, 'ELECTRICAL_GENERATOR_3', 1)
	pushSeqCmd(dt, 'ELECTRICAL_GENERATOR_4', 1)

	# MC + MW silence cycles before BEFORE TAXI (~15s coverage).
	mc_mw_silence(3, label='before BEFORE TAXI')

	# ===========================================================================
	# CHECKLIST: BEFORE TAXI
	# ===========================================================================

	# Propeller control switches AUTO (already at NORMAL/center which is the AUTO/middle)
	pushSeqCmd(dt, 'PROP_CTRL_1', 1)
	pushSeqCmd(dt, 'PROP_CTRL_2', 1)
	pushSeqCmd(dt, 'PROP_CTRL_3', 1)
	pushSeqCmd(dt, 'PROP_CTRL_4', 1)

	# Radar - ON
	pushSeqCmd(dt, 'RCP_MASTER_POWER', 1, 'Radar - ON')

	# ICE PROTECTION propellers - AUTO (center position)
	pushSeqCmd(dt, 'ICE_PROP_1', 1, 'Prop ice 1 - AUTO')
	pushSeqCmd(dt, 'ICE_PROP_2', 1)
	pushSeqCmd(dt, 'ICE_PROP_3', 1)
	pushSeqCmd(dt, 'ICE_PROP_4', 1)

	# Wait for alignment if not done yet
	pushSeqCmd(dt, 'scriptTimerEnd', name='align')

	# MC + MW silence cycles during BEFORE TAXI (~10s coverage).
	mc_mw_silence(2, label='BEFORE TAXI')


	# ===========================================================================
	# CHECKLIST: TAXI
	# ===========================================================================

	# Taxi & wingtip taxi lights ON
	pushSeqCmd(dt, 'TAXI_LIGHT', 1, 'Taxi lights - ON')
	pushSeqCmd(dt, 'WINGTIP_TAXI', 1, 'Wingtip taxi - ON')

	# FLAPS 50%
	pushSeqCmd(dt, 'CC_FLAP_LEVER', int16(0.50), 'Flaps - 50%')


	# MC + MW silence cycles before BEFORE TAKEOFF (~30s coverage —
	# BEFORE TAKEOFF is the longest single phase: CNI defensive setup,
	# HUD config, ARC-210, standby ADI alignment, ATCS reassert).
	mc_mw_silence(6, label='before BEFORE TAKEOFF')

	# ===========================================================================
	# CHECKLIST: BEFORE TAKEOFF
	# ===========================================================================

	# PITOT/NESA HEAT switches - ON
	pushSeqCmd(dt, 'ICE_PITOT_P', 1, 'Pilot pitot heat - ON')
	pushSeqCmd(dt, 'ICE_PITOT_CP', 1, 'Copilot pitot heat - ON')
	pushSeqCmd(dt, 'ICE_NESA_CTR', 1, 'NESA center - ON')
	pushSeqCmd(dt, 'ICE_NESA_SIDE', 1, 'NESA side - ON')

	# Lights - Set
	pushSeqCmd(dt, 'LDG_MOTOR_L', 2, 'L landing motor - EXTEND')
	pushSeqCmd(dt, 'LDG_MOTOR_R', 2, 'R landing motor - EXTEND')
	# Strobes were RED for engine start, leave at RED for takeoff
	pushSeqCmd(dt, 'EXT_LEDGE', 1, 'Leading edge - ON')

	# FUEL MANAGEMENT - all transfer OFF, all crossfeed CLOSED (verified)
	for tank in ('MAIN_1','MAIN_2','MAIN_3','MAIN_4','AUX_L','AUX_R','EXT_L','EXT_R'):
		pushSeqCmd(dt, f'FUEL_XFER_{tank}', 1)
	pushSeqCmd(dt, 'FUEL_XFEED_ENG_1', 0)
	pushSeqCmd(dt, 'FUEL_XFEED_ENG_2', 0)
	pushSeqCmd(dt, 'FUEL_XFEED_ENG_3', 0)
	pushSeqCmd(dt, 'FUEL_XFEED_ENG_4', 0)
	pushSeqCmd(dt, 'FUEL_XFEED_SHIP', 0)

	# --- CNI-MU defensive systems configuration ---
	# Every CNI key is a press (1) + release (0) pair, like a mouse click —
	# press-only leaves the key held down indefinitely and the CNI can then
	# swallow the next press of the same key.
	#
	# ROBUSTNESS: navigation is ABSOLUTE, not relative. MC INDX always lands
	# on MSN CMPTR INDEX and R1 there always opens DEF SYS CTRL, so the walk
	# re-anchors through MC INDX -> R1 before each sub-page visit instead of
	# trusting relative "back" hops. Why it matters: if a page-branch press
	# gets dropped while the CNI is redrawing, the following presses land on
	# the WRONG page — and on DEF SYS CTRL, L4/L5 are the MWS/IRCM POWER
	# toggles, so a mis-landed "arm" press powers a subsystem OFF. The L1
	# MSTR PWR toggle then displays OFF (it reflects overall subsystem
	# state), i.e. the defensive systems die mid-start. Every page change
	# also gets >= 1.0s to settle before the next press for the same reason.
	#
	# Page flow (pilot CNI):
	#   MC INDX -> MSN CMPTR INDEX -> R1 -> DEF SYS CTRL -> L1 (MSTR PWR ON)
	#   re-anchor -> DEF SYS CTRL -> L3 -> CMDS: L3 (OTHER1), L4 (OTHER2), L5 (JMR INTF)
	#   re-anchor -> DEF SYS CTRL -> L2 -> RWR:  R2 (SHOW UNK)
	#   MC INDX -> back out

	# Dismiss anything currently on R4/R5 (e.g. a residual scratchpad prompt)
	pushSeqCmd(dt,  'PLT_CNI_LSK_R4', 1, 'PLT CNI LSK R4 - press')
	pushSeqCmd(0.3, 'PLT_CNI_LSK_R4', 0, 'PLT CNI LSK R4 - release')
	pushSeqCmd(dt,  'PLT_CNI_LSK_R5', 1, 'PLT CNI LSK R5 - press')
	pushSeqCmd(0.3, 'PLT_CNI_LSK_R5', 0, 'PLT CNI LSK R5 - release')

	# Navigate (absolute): MC INDX -> MSN CMPTR INDEX -> DEF SYS> (R1)
	pushSeqCmd(dt,  'PLT_CNI_MC_INDX', 1, 'PLT CNI - to MSN CMPTR INDEX')
	pushSeqCmd(0.3, 'PLT_CNI_MC_INDX', 0)
	pushSeqCmd(1.0, 'PLT_CNI_LSK_R1',  1, 'MSN CMPTR INDEX R1 - DEF SYS>')
	pushSeqCmd(0.3, 'PLT_CNI_LSK_R1',  0)

	# DEF SYS CTRL: press MSTR PWR (L1) — this is a cascading master that
	# powers MWS, IRCM and the rest of the defensive systems automatically.
	# Do NOT press L4 (MWS PWR) or L5 (IRCM PWR) afterwards — they're already
	# ON once MSTR PWR is engaged, and pressing them would toggle them back
	# OFF, which is what causes the "CMDS audio tones silent on cold start"
	# bug we previously hit.
	pushSeqCmd(1.0, 'PLT_CNI_LSK_L1', 1, 'DEF SYS L1 - MSTR PWR ON (cascades to MWS + IRCM)')
	pushSeqCmd(0.3, 'PLT_CNI_LSK_L1', 0)
	# Let MSTR PWR settle so the cascade lands on MWS / IRCM / CMDS before
	# we navigate to the sub-pages.
	pushSeqCmd(2.0, '', '', 'Wait for MSTR PWR cascade')

	# Re-anchor to a known page state before the CMDS walk.
	pushSeqCmd(dt,  'PLT_CNI_MC_INDX', 1, 'Re-anchor: MC INDX')
	pushSeqCmd(0.3, 'PLT_CNI_MC_INDX', 0)
	pushSeqCmd(1.0, 'PLT_CNI_LSK_R1',  1, 'Re-anchor: R1 - DEF SYS>')
	pushSeqCmd(0.3, 'PLT_CNI_LSK_R1',  0)

	# CMDS sub-page (L3 from DEF SYS CTRL): arm OTHER1/OTHER2 and toggle JMR INTF ON.
	# Defaults are OTHER1/2 SAFE + JMR INTF OFF, so a single press flips each.
	pushSeqCmd(1.0, 'PLT_CNI_LSK_L3', 1, 'DEF SYS L3 - to CMDS page')
	pushSeqCmd(0.3, 'PLT_CNI_LSK_L3', 0)
	pushSeqCmd(1.0, 'PLT_CNI_LSK_L3', 1, 'CMDS L3 - OTHER1 ARM')
	pushSeqCmd(0.3, 'PLT_CNI_LSK_L3', 0)
	pushSeqCmd(0.5, 'PLT_CNI_LSK_L4', 1, 'CMDS L4 - OTHER2 ARM')
	pushSeqCmd(0.3, 'PLT_CNI_LSK_L4', 0)
	pushSeqCmd(0.5, 'PLT_CNI_LSK_L5', 1, 'CMDS L5 - JMR INTF ON')
	pushSeqCmd(0.3, 'PLT_CNI_LSK_L5', 0)

	# Re-anchor to a known page state before the RWR walk (replaces the old
	# relative "L6 back" hops, which broke the rest of the walk if dropped).
	pushSeqCmd(0.5, 'PLT_CNI_MC_INDX', 1, 'Re-anchor: MC INDX')
	pushSeqCmd(0.3, 'PLT_CNI_MC_INDX', 0)
	pushSeqCmd(1.0, 'PLT_CNI_LSK_R1',  1, 'Re-anchor: R1 - DEF SYS>')
	pushSeqCmd(0.3, 'PLT_CNI_LSK_R1',  0)

	# RWR sub-page (L2 from DEF SYS CTRL): toggle SHOW UNK on, then run the
	# RWR self-tests (R4 = AUDIO TEST, R5 = MSL LAUNCH TEST — momentary,
	# single press+release each).
	pushSeqCmd(1.0, 'PLT_CNI_LSK_L2', 1, 'DEF SYS L2 - to RWR page')
	pushSeqCmd(0.3, 'PLT_CNI_LSK_L2', 0)
	pushSeqCmd(1.0, 'PLT_CNI_LSK_R2', 1, 'RWR R2 - SHOW UNK toggle')
	pushSeqCmd(0.3, 'PLT_CNI_LSK_R2', 0)
	pushSeqCmd(0.8, 'PLT_CNI_LSK_R4', 1, 'RWR R4 - AUDIO TEST')
	pushSeqCmd(0.3, 'PLT_CNI_LSK_R4', 0)
	pushSeqCmd(0.8, 'PLT_CNI_LSK_R5', 1, 'RWR R5 - MSL LAUNCH TEST')
	pushSeqCmd(0.3, 'PLT_CNI_LSK_R5', 0)

	# Back out to MSN CMPTR INDEX (absolute, single hop is enough)
	pushSeqCmd(0.5, 'PLT_CNI_MC_INDX', 1, 'PLT CNI MC INDX - back out')
	pushSeqCmd(0.3, 'PLT_CNI_MC_INDX', 0)

	# Defensive systems master OPR for takeoff (clears CMDS FAIL warning)
	# DSP_DEFENSIVE_MASTER_SWITCH/ECM/IRCM positions: 0=STBY, 1=OPR
	# DSP_CMDS_MODE positions: 0=STBY, 1=MAN, 2=SEMI, 3=AUTO, 4=BYP
	pushSeqCmd(dt, 'DSP_CMS_JETTISON_GUARD', 0, 'CMS Jettison guard - down (verify)')
	pushSeqCmd(dt, 'DSP_CMS_JETTISON_SWITCH', 0, 'CMS Jettison - OFF (verify)')
	pushSeqCmd(dt, 'DSP_DEFENSIVE_MASTER_SWITCH', 1, 'Defensive master - OPR')
	pushSeqCmd(dt, 'DSP_ECM_MASTER', 1, 'ECM - OPR')
	pushSeqCmd(dt, 'DSP_IRCM_MASTER', 1, 'IRCM - OPR')
	pushSeqCmd(dt, 'DSP_CMDS_MODE', 3, 'CMDS - AUTO')
	pushSeqCmd(dt, 'DSP_RWR_TGT_SEP', 1, 'RWR TGT SEP - press')
	pushSeqCmd(dt, 'DSP_RWR_SRCH', 1, 'RWR SRCH - press')

	# Pilot RWR volume: pull the knob out to monitor (right-click in game),
	# then rotate to the 50% point.
	pushSeqCmd(dt, 'PLT_ICS_RWR_BUTTON', 1, 'Pilot RWR volume knob - PULL to monitor')
	pushSeqCmd(dt, 'PLT_ICS_RWR_VOLUME', int16(0.50), 'Pilot RWR volume - 50%')

	# MC + MW silence cycles after defensive systems OPR (~15s coverage
	# through ADP computer drop, HUD config, ARC-210 setup).
	mc_mw_silence(3, label='post defensive')

	# --- Computer drop switch to AD-MAN/TJ-AUTO (middle position) ---
	pushSeqCmd(dt, 'ADP_COMP_DROP', 1, 'Computer Drop - AD-MAN/TJ-AUTO')

	# --- Pilot HUD: latch, TAC mode, NAV mode ---
	pushSeqCmd(dt, '', '', 'announcement removed')
	pushSeqCmd(dt, 'PLT_HUD_LATCH',    1, 'Pilot HUD Latch - press')
	pushSeqCmd(dt, 'PLT_HUD_TAC_MODE', 1, 'Pilot HUD TAC mode - press')
	pushSeqCmd(dt, 'PLT_HUD_NAV_MODE', 1, 'Pilot HUD NAV mode - press')

	# --- Day exterior lighting state (Day profile only) ---
	# The Night-mode block further below handles Time = Night instead.
	# Day config: taxi / wingtip taxi / landing light motors DOWN,
	# Covert/Formation brightness MAX, nav lights STEADY, exterior master NORM.
	if vars.get('Time') != 'Night':
		pushSeqCmd(dt, 'TAXI_LIGHT',   0, 'Taxi lights - DOWN (day)')
		pushSeqCmd(dt, 'WINGTIP_TAXI', 0, 'Wingtip taxi - DOWN (day)')
		pushSeqCmd(dt, 'LDG_MOTOR_L',  0, 'L landing motor - DOWN/RETRACT (day)')
		pushSeqCmd(dt, 'LDG_MOTOR_R',  0, 'R landing motor - DOWN/RETRACT (day)')
		pushSeqCmd(dt, 'EXT_FORM_BRT', int16(1.0), 'Covert/Formation brightness - MAX (day)')
		pushSeqCmd(dt, 'EXT_NAV',      0, 'Nav lights - STEADY/down (day)')
		pushSeqCmd(dt, 'EXT_DIM',      0, 'Nav lights brightness - DOWN (day)')
		pushSeqCmd(dt, 'EXT_LEDGE',    0, 'Leading edge - DOWN (day)')
		pushSeqCmd(dt, 'EXT_MASTER',   0, 'Exterior master - NORM/down (day)')

	# --- ARC-210: TR+G + SQL on ---
	pushSeqCmd(dt, '', '', 'announcement removed')
	pushSeqCmd(dt, 'ARC210_OP_MODE', 1, 'ARC-210 op mode - TR+G')
	pushSeqCmd(dt, 'ARC210_SQL',     1, 'ARC-210 SQL - ON')

	# --- Standby ADI: cage then uncage to align ---
	pushSeqCmd(dt, '', '', 'announcement removed')
	pushSeqCmd(dt, 'STBY_ADI_CAGE', 1, 'Standby ADI - cage')
	pushSeqCmd(1.0, 'STBY_ADI_CAGE', 0, 'Standby ADI - uncage (release)')
	# Rotate the standby ADI pitch bias adjust just a smidge so the
	# instrument actually uncages (all profiles).
	pushSeqCmd(0.5, 'STBY_ADI_PITCH_BIAS', '+3200', 'Standby ADI bias adjust - nudge to uncage')

	# Re-assert ATCS in case it got toggled off (clears ATCS OFF warning)
	pushSeqCmd(dt, 'ATCS_GUARD', 1, 'ATCS guard - up')
	pushSeqCmd(dt, 'ATCS', 1, 'ATCS - ON (re-assert)')
	pushSeqCmd(dt, 'ATCS_GUARD', 0, 'ATCS guard - down')

	# Night mode:
	#   - All internal cockpit lights OFF (panel/console/dome/flood/floor backlights)
	#   - All display screen brightness to lowest visible
	#   - All external lights ON (NAV steady bright, landing, taxi, leading edge)
	if vars.get('Time') == 'Night':
		pushSeqCmd(dt, '', '', 'announcement removed')

		# --- Internal cockpit lights OFF ---
		# Pilot side panel/console/dome/flood/floor
		pushSeqCmd(dt, 'PLT_CC_LIGHTING_PANEL_BACKLIGHTING',       int16(0.0), 'PLT panel backlight - OFF')
		pushSeqCmd(dt, 'PLT_CC_LIGHTING_DOME_BRIGHTNESS',          int16(0.0), 'PLT dome - OFF')
		pushSeqCmd(dt, 'PLT_CC_LIGHTING_CB_BRIGHTNESS',            int16(0.0), 'PLT CB lights - OFF')
		pushSeqCmd(dt, 'PLT_CC_LIGHTING_FLOOD_LIGHT_BRIGHTNESS',   int16(0.0), 'PLT flood - OFF')
		pushSeqCmd(dt, 'PLT_CC_LIGHTING_FLOOR_LIGHT_BRIGHTNESS',   int16(0.0), 'PLT floor - OFF')
		# Copilot side panel/console/overhead/flood
		# CPLT panel backlight quirk: a raw 0 value wraps the knob to FULL BRIGHT
		# instead of OFF. Push it a fraction above 0 to land at "essentially off".
		pushSeqCmd(dt, 'CPLT_CC_LIGHTING_PANEL_BACKLIGHTING',          int16(0.03), 'CPLT panel backlight - near OFF')
		pushSeqCmd(dt, 'CPLT_CC_LIGHTING_OVERHEAD_PANEL_BACKLIGHTING', int16(0.0), 'CPLT overhead backlight - OFF')
		pushSeqCmd(dt, 'CPLT_CC_LIGHTING_CONSOLE_LIGHT_BRIGHTNESS',    int16(0.0), 'CPLT console - OFF')
		pushSeqCmd(dt, 'CPLT_CC_LIGHTING_OVERHEAD_FLOOD_LIGHT_BRIGHTNESS', int16(0.0), 'CPLT overhead flood - OFF')
		pushSeqCmd(dt, 'CPLT_CC_LIGHTING_FLOOD_LIGHT_BRIGHTNESS',      int16(0.0), 'CPLT flood - OFF')
		pushSeqCmd(dt, 'CPLT_CC_LIGHTING_CB_BRIGHTNESS',               int16(0.0), 'CPLT CB lights - OFF')

		# --- Display screens to lowest brightness ---
		# Master display brightness knobs (drives HDDs/HUDs)
		pushSeqCmd(dt, 'PLT_CC_LIGHTING_MASTER_DISPLAY_BRIGHTNESS',  int16(0.05), 'PLT master display - LOW')
		pushSeqCmd(dt, 'CPLT_CC_LIGHTING_MASTER_DISPLAY_BRIGHTNESS', int16(0.05), 'CPLT master display - LOW')

		# CNI-MU brightness rockers - click DECREASE 7 times to take all the way down
		# (rocker: 0=DECREASE, 1=OFF/center, 2=INCREASE; momentary so press+release each click)
		for i in range(1, 8):
			pushSeqCmd(0.2, 'PLT_CNI_BRT_ROCKER',  0, f'PLT CNI BRT - decrease click {i}/7')
			pushSeqCmd(0.2, 'PLT_CNI_BRT_ROCKER',  1)
		for i in range(1, 8):
			pushSeqCmd(0.2, 'CPLT_CNI_BRT_ROCKER', 0, f'CPLT CNI BRT - decrease click {i}/7')
			pushSeqCmd(0.2, 'CPLT_CNI_BRT_ROCKER', 1)

		# --- External lights ON ---
		pushSeqCmd(dt, 'EXT_NAV',        0, 'NAV lights - STEADY/down (night)')
		pushSeqCmd(dt, 'EXT_DIM',        1, 'NAV brightness - BRIGHT')
		pushSeqCmd(dt, 'EXT_LEDGE',      1, 'Leading edge - ON')
		pushSeqCmd(dt, 'LDG_LIGHT_L',    1, 'L landing light - ON')
		pushSeqCmd(dt, 'LDG_LIGHT_R',    1, 'R landing light - ON')
		pushSeqCmd(dt, 'TAXI_LIGHT',     1, 'Taxi - ON')
		pushSeqCmd(dt, 'WINGTIP_TAXI',   1, 'Wingtip taxi - ON')
		pushSeqCmd(dt, 'EXT_STROBE_TOP', 0, 'Top strobe - RED (night safe)')
		pushSeqCmd(dt, 'EXT_STROBE_BTM', 0, 'Bottom strobe - RED (night safe)')
		# Final switch for night config: Exterior Lighting Master to NORM (down/0)
		pushSeqCmd(dt, 'EXT_MASTER',     0, 'EXT master - NORM (down)')

	# --- Pilot HUD brightness AUTO ---
	# Pull for AUTO (left click on knob = pull).
	# HDD page setup is left to the pilot (display layout is a personal preference).
	# Prop sync is asserted at the very end, after FADEC guards close.
	pushSeqCmd(dt, 'PLT_HUD_BRT_AUTO', 1, 'Pilot HUD brightness - pull for AUTO')

	# MC + MW silence cycles before final actions (~15s coverage
	# through ATCS down, pitot/NESA, FADEC guards).
	# (LSGI was moved to the very end of the script — see below — so it
	# fires after AUTONAV / MSTR AV ON when engines are fully stable.)
	mc_mw_silence(3, label='before final actions')

	# --- FINAL switch positions (DOWN) ---
	# ATCS down (engines are running, safe to disengage now)
	pushSeqCmd(dt, 'ATCS_GUARD', 1, 'ATCS guard - up')
	pushSeqCmd(dt, 'ATCS',       0, 'ATCS - DOWN')
	pushSeqCmd(dt, 'ATCS_GUARD', 0, 'ATCS guard - down')
	# Pitot/NESA heat switches DOWN
	pushSeqCmd(dt, 'ICE_PITOT_P',   0, 'Pilot pitot heat - DOWN')
	pushSeqCmd(dt, 'ICE_PITOT_CP',  0, 'Copilot pitot heat - DOWN')
	pushSeqCmd(dt, 'ICE_NESA_CTR',  0, 'NESA center - DOWN')
	pushSeqCmd(dt, 'ICE_NESA_SIDE', 0, 'NESA side/lower - DOWN')
	# Engine FADEC switch guards DOWN (closed)
	pushSeqCmd(dt, 'FADEC_GUARD_1', 1, 'Engine 1 FADEC guard - UP')
	pushSeqCmd(dt, 'FADEC_GUARD_2', 1, 'Engine 2 FADEC guard - UP')
	pushSeqCmd(dt, 'FADEC_GUARD_3', 1, 'Engine 3 FADEC guard - UP')
	pushSeqCmd(dt, 'FADEC_GUARD_4', 1, 'Engine 4 FADEC guard - UP')
	# (PROP_SYNC engagement is deferred to the very end of the script — after
	# AUTONAV / MSTR AV ON — so engines are fully spooled and stable.)

	# Final warning suppression: hammer BOTH pilot AND copilot MC and MW buttons
	# in three spaced-out cycles. The audio tone re-triggers if any warning
	# condition reasserts between presses, so we repeat to catch lingering ones.
	for cycle_dt, label in ((dt, '1/3'), (0.6, '2/3'), (0.8, '3/3')):
		pushSeqCmd(cycle_dt, 'PLT_MASTER_CAUTION',  1, f'PLT MC final {label}')
		pushSeqCmd(0.2,      'PLT_MASTER_CAUTION',  0)
		pushSeqCmd(0.2,      'CPLT_MASTER_CAUTION', 1, f'CPLT MC final {label}')
		pushSeqCmd(0.2,      'CPLT_MASTER_CAUTION', 0)
		pushSeqCmd(0.2,      'PLT_MASTER_WARNING',  1, f'PLT MW final {label}')
		pushSeqCmd(0.2,      'PLT_MASTER_WARNING',  0)
		pushSeqCmd(0.2,      'CPLT_MASTER_WARNING', 1, f'CPLT MW final {label}')
		pushSeqCmd(0.2,      'CPLT_MASTER_WARNING', 0)

	# Final announcements
	pushSeqCmd(dt, '', '', 'announcement removed')
	pushSeqCmd(0.5, '', '', 'announcement removed')
	pushSeqCmd(0.5, '', '', 'announcement removed')
	pushSeqCmd(0.5, '', '', 'announcement removed')

	# --- FINAL: Navigate both CNI-MUs to POWER UP, then engage AUTONAV + MSTR AV ON ---
	# POWER UP page is reached via INDX (INDEX 1/2) -> L1 (<POWER UP).
	# Page layout (per CNI_MU/pages/power_up.lua):
	#   L5 = ALIGN GPS/LAST/REF toggle
	#   R4 = MSTR AV ON   (toggle)
	#   R5 = AUTONAV      (toggle)
	# Pilot AND copilot must both be on POWER UP with position synced (GPS) before
	# AUTONAV / MSTR AV ON. These are the VERY LAST actions of the cold start.
	pushSeqCmd(0.5, 'scriptSpeech', 'G P S alignment ongoing. E T A five minutes from startup. Check HUD to verify a true heading reading.')

	# Pilot CNI -> POWER UP
	pushSeqCmd(dt,  'PLT_CNI_INDX',   1, 'PLT CNI INDX - to INDEX')
	pushSeqCmd(0.3, 'PLT_CNI_INDX',   0)
	pushSeqCmd(0.5, 'PLT_CNI_LSK_L1', 1, 'PLT CNI L1 - <POWER UP')
	pushSeqCmd(0.3, 'PLT_CNI_LSK_L1', 0)

	# Copilot CNI -> POWER UP
	pushSeqCmd(0.5, 'CPLT_CNI_INDX',   1, 'CPLT CNI INDX - to INDEX')
	pushSeqCmd(0.3, 'CPLT_CNI_INDX',   0)
	pushSeqCmd(0.5, 'CPLT_CNI_LSK_L1', 1, 'CPLT CNI L1 - <POWER UP')
	pushSeqCmd(0.3, 'CPLT_CNI_LSK_L1', 0)

	pushSeqCmd(0.5, '', '', 'announcement removed')

	# --- Final actions: AUTONAV select, then MSTR AV ON select, on both CNIs ---
	pushSeqCmd(0.5, '', '', 'announcement removed')
	pushSeqCmd(0.5, 'PLT_CNI_LSK_R5',  1, 'PLT CNI R5 - AUTONAV select')
	pushSeqCmd(0.3, 'PLT_CNI_LSK_R5',  0)
	pushSeqCmd(0.3, 'CPLT_CNI_LSK_R5', 1, 'CPLT CNI R5 - AUTONAV select')
	pushSeqCmd(0.3, 'CPLT_CNI_LSK_R5', 0)

	pushSeqCmd(0.5, '', '', 'announcement removed')
	pushSeqCmd(0.5, 'PLT_CNI_LSK_R4',  1, 'PLT CNI R4 - MSTR AV ON select')
	pushSeqCmd(0.3, 'PLT_CNI_LSK_R4',  0)
	pushSeqCmd(0.3, 'CPLT_CNI_LSK_R4', 1, 'CPLT CNI R4 - MSTR AV ON select')
	pushSeqCmd(0.3, 'CPLT_CNI_LSK_R4', 0)

	# --- LSGI (Low Speed Ground Idle) select switches - quick press + release ---
	# LSGI is a quick click — press value 1 then immediately release value 0.
	# Both events together complete the click cycle and activate LSGI; the
	# release is what triggers the activation (press alone just visually
	# depresses the button).
	#
	# Placed here as one of the last actions so engines are fully spooled and
	# stable. Engines 1 and 2 still get a longer pre-press delay (~1.5s) —
	# their FADECs occasionally refuse the LSGI input if pressed back-to-back.
	pushSeqCmd(1.0, '', '', 'announcement removed')

	# Engine 1: 1.5s pre-press, slightly longer hold (0.5s).
	# The first LSGI click in the sequence seems to need a bit more hold
	# time than the rest (likely cold-cache / first-click lag). Engines
	# 2-4 work reliably with a 0.1s quick click.
	pushSeqCmd(1.5,  'CC_LSGI_ENGINE_1_SWITCH', 1, 'Engine 1 LSGI - press')
	pushSeqCmd(0.5,  'CC_LSGI_ENGINE_1_SWITCH', 0, 'Engine 1 LSGI - release (activate)')

	# Engine 2: 1.5s pre-press, quick press+release (0.1s)
	pushSeqCmd(1.5,  'CC_LSGI_ENGINE_2_SWITCH', 1, 'Engine 2 LSGI - press')
	pushSeqCmd(0.1,  'CC_LSGI_ENGINE_2_SWITCH', 0, 'Engine 2 LSGI - release (activate)')

	# Engine 3: 0.5s pre-press, quick press+release (0.1s)
	pushSeqCmd(0.5,  'CC_LSGI_ENGINE_3_SWITCH', 1, 'Engine 3 LSGI - press')
	pushSeqCmd(0.1,  'CC_LSGI_ENGINE_3_SWITCH', 0, 'Engine 3 LSGI - release (activate)')

	# Engine 4: 0.5s pre-press, quick press+release (0.1s)
	pushSeqCmd(0.5,  'CC_LSGI_ENGINE_4_SWITCH', 1, 'Engine 4 LSGI - press')
	pushSeqCmd(0.1,  'CC_LSGI_ENGINE_4_SWITCH', 0, 'Engine 4 LSGI - release (activate)')

	# --- Absolute last action: engage Prop Sync ---
	# By this point all four engines have been running for several minutes
	# through BEFORE TAXI / TAXI / BEFORE TAKEOFF and are fully spooled and
	# stable. Earlier attempts to engage prop sync (pre-battery or right
	# after FADEC guards close) can be silently rejected by the system if
	# engine state hasn't settled, so the engagement is performed here as
	# the final functional action of the cold start.
	pushSeqCmd(1.0, '', '', 'announcement removed')
	pushSeqCmd(0.5, 'PROP_SYNC', 0, 'Prop sync - OFF/down')

	# Release the APU bleed air push button - it stays visually stuck in the
	# pressed position from the APU start unless clicked back out. Engines
	# supply bleed air by now, so releasing (closing APU bleed) is correct.
	pushSeqCmd(0.5, 'BLEED_APU', 0, 'APU bleed button - release/out (close)')

	# =====================================================================
	# PILOT AMU / HDD DISPLAY CONFIGURATION
	# =====================================================================
	# Done at the very end so all display/avionics systems are powered.
	#
	# AMU MODEL (decoded from the mod's AMU_CNBP page files + manual):
	#   The pilot AMU has TWO screens. The MAIN MENU spans both:
	#     LEFT screen  (PLT_AMU_L_*) = main_menu_1: <PFD <ENGINE <CAPS |
	#                   NAV-RADAR>(R1) SYS STATUS>(R2) DIG MAP>(R3) TAWS>(R4)
	#     RIGHT screen (PLT_AMU_R_*) = main_menu_2: <NAV SELECT <ACAWS
	#                   <DIAGNOSTICS <PREFLIGHT | DEFAULTS>(R1) --(R2)
	#                   LIGHTING>(R3) GCAS/TAWS AND STALL>(R4)
	#   A page renders on the SAME screen it was selected from; its sub-pages
	#   (HDD POS / RANGE / OVERLAYS) render on the OTHER screen. When a display
	#   page is selected, HDD POS auto-appears on the other screen.
	#   LSK order in every page: L1 L2 L3 L4 then R1 R2 R3 R4.
	#
	#   DISPLAY page (NAV-RADAR/TAWS): L-screen R1=RANGE> R2=OVERLAYS>
	#       R3=HDD POS> R4=MAIN MENU>.  DIG MAP: R1=color, R2=OVERLAYS>,
	#       R3=HDD POS>, R4=MAIN MENU> (no range).
	#   HDD POS sub-page (R-screen): L1=HDD1 L2=HDD2 L3=HDD3 L4=HDD4.
	#   RANGE sub-page (R-screen): R2=40(8)  R3=80(16).
	#   OVERLAYS sub-page (R-screen): L2=TACTICAL  R2=RWR  R4=CLEAR ALL.
	#   GCAS/TAWS page (from main_menu_2 R4, renders on R-screen):
	#       L1=NORMAL/TACTICAL  R1=POPUP INHIBIT  R2=TERR INHIBIT  R4=MAIN MENU>.
	#
	# All keys press(1)+release(0) like the CNI. 1.2s settle after each page
	# change (AMU redraw). Assumes the AMU is at MAIN MENU to start (power-on
	# default) and that toggles start from their default state (one press =
	# desired state). VERIFY on first run; if presses hit the wrong screen the
	# two screens are swapped -> flip PLT_AMU_L_* <-> PLT_AMU_R_*.
	pushSeqCmd(1.0, 'scriptSpeech', 'Configuring pilot displays.')

	def amu(dt_, key, msg=''):
		# key like 'L_R1' -> PLT_AMU_L_R1; press + release
		pushSeqCmd(dt_, f'PLT_AMU_{key}', 1, msg)
		pushSeqCmd(0.15, f'PLT_AMU_{key}', 0)

	# --- TAWS -> HDD2, RANGE 40, RWR overlay ---
	amu(0.6, 'L_R4', 'MAIN MENU L-R4 - TAWS> (select TAWS onto L screen)')
	amu(0.6, 'R_L2', 'HDD POS R-L2 - HDD 2')            # HDD POS auto on R screen
	amu(0.6, 'L_R1', 'TAWS DISPLAY L-R1 - RANGE>')
	amu(0.6, 'R_R2', 'RANGE R-R2 - 40 (8)')
	amu(0.6, 'L_R2', 'TAWS DISPLAY L-R2 - OVERLAYS>')
	amu(0.6, 'R_R2', 'OVERLAYS R-R2 - RWR enable')
	amu(0.6, 'L_R4', 'TAWS DISPLAY L-R4 - MAIN MENU> (back)')

	# --- DIG MAP -> HDD3 (no further edits) ---
	amu(0.6, 'L_R3', 'MAIN MENU L-R3 - DIG MAP> (select onto L screen)')
	amu(0.6, 'R_L3', 'HDD POS R-L3 - HDD 3')
	amu(0.6, 'L_R4', 'DIG MAP DISPLAY L-R4 - MAIN MENU> (back)')

	# --- NAV-RADAR -> HDD1, RANGE 80, RWR overlay ---
	amu(0.6, 'L_R1', 'MAIN MENU L-R1 - NAV-RADAR> (select onto L screen)')
	amu(0.6, 'R_L1', 'HDD POS R-L1 - HDD 1')
	amu(0.6, 'L_R1', 'NAV-RADAR DISPLAY L-R1 - RANGE>')
	amu(0.6, 'R_R3', 'RANGE R-R3 - 80 (16)')
	amu(0.6, 'L_R2', 'NAV-RADAR DISPLAY L-R2 - OVERLAYS>')
	amu(0.6, 'R_R2', 'OVERLAYS R-R2 - RWR enable')
	amu(0.6, 'L_R4', 'NAV-RADAR DISPLAY L-R4 - MAIN MENU> (back)')

	# --- GCAS/TAWS: TACTICAL on, POPUP INHIBIT on, TERR INHIBIT on ---
	# Selected from main_menu_2 (RIGHT screen) R4, but the page itself renders
	# on the LEFT screen (the active-page screen — same as the display pages),
	# so all of its option keys are PLT_AMU_L_*. (Confirmed by test: the
	# NORMAL/TACTICAL toggle appears on the left AMU.)
	amu(0.6, 'R_R4', 'MAIN MENU R-R4 - GCAS/TAWS AND STALL> (select; page opens on L screen)')
	amu(0.6, 'L_L1', 'GCAS/TAWS L-L1 - NORMAL/TACTICAL -> TACTICAL')
	amu(0.6, 'L_R1', 'GCAS/TAWS L-R1 - POPUP INHIBIT on')
	amu(0.6, 'L_R2', 'GCAS/TAWS L-R2 - TERR INHIBIT on')
	amu(0.6, 'L_R4', 'GCAS/TAWS L-R4 - MAIN MENU> (back)')

	pushSeqCmd(0.5, 'scriptSpeech', 'Cold start complete.')

	return seq


###############################################################################
# SHUTDOWN
###############################################################################
def Shutdown(config, vars):
	seq = []
	seqTime = 0
	# Rapid-fire shutdown — all switches fire near-instantly. Steps that
	# genuinely need to wait (APU spring release, APU_NG telemetry, etc.)
	# pass their own explicit time value below.
	dt = 0.02

	def pushSeqCmd(dt, cmd, *args, **kwargs):
		nonlocal seq, seqTime
		if len(args):
			seq.append({
				'time': round(dt, 2),
				'cmd': cmd,
				'arg': args[0],
				'msg': args[1] if len(args) > 1 else '',
			})
		else:
			step = {
				'time': round(dt, 2),
				'cmd': cmd,
			}
			for key in kwargs:
				step[key] = kwargs[key]
			seq.append(step)

	pushSeqCmd(0, '', '', "C-130J Shutdown sequence")
	pushSeqCmd(dt, 'scriptSpeech', 'Shutting down.')

	# Simple shutdown - rapid fire, no delays.
	# 1. All 4 engine start switches to STOP (one detent LEFT = value 0).
	pushSeqCmd(dt, 'ENG_1_START_SWITCH', 0, 'Engine 1 - click LEFT to STOP')
	pushSeqCmd(dt, 'ENG_2_START_SWITCH', 0, 'Engine 2 - click LEFT to STOP')
	pushSeqCmd(dt, 'ENG_3_START_SWITCH', 0, 'Engine 3 - click LEFT to STOP')
	pushSeqCmd(dt, 'ENG_4_START_SWITCH', 0, 'Engine 4 - click LEFT to STOP')

	# Prop sync switch UP (value 1). Given a real delay (not the 0.02s rapid
	# fire) so the command isn't dropped — that drop is why it appeared stuck
	# down at both values before.
	pushSeqCmd(0.3, 'PROP_SYNC', 1, 'Prop sync - UP')

	# ATCS flipped UP to OFF (down=ON, up=OFF; value 1 = up). Under a guard.
	pushSeqCmd(0.3, 'ATCS_GUARD', 1, 'ATCS guard - up')
	pushSeqCmd(0.3, 'ATCS', 1, 'ATCS - UP (OFF)')
	pushSeqCmd(0.3, 'ATCS_GUARD', 0, 'ATCS guard - down')

	# 2. APU start switch to OFF/STOP (left click).
	pushSeqCmd(dt, 'APU_SWITCH', 0, 'APU switch - OFF/STOP')

	# 3. External Power/APU switch to middle OFF position.
	pushSeqCmd(dt, 'ELECTRICAL_EXT_POWER_APU', 1, 'EXT PWR/APU - OFF (middle)')

	# 4. Battery switch UP to OFF (right click).
	pushSeqCmd(dt, 'ELECTRICAL_BATTERY', 0, 'Battery - OFF (up)')

	# 5. Generators 1-4 OFF (right click).
	pushSeqCmd(dt, 'ELECTRICAL_GENERATOR_1', 0, 'Gen 1 - OFF')
	pushSeqCmd(dt, 'ELECTRICAL_GENERATOR_2', 0, 'Gen 2 - OFF')
	pushSeqCmd(dt, 'ELECTRICAL_GENERATOR_3', 0, 'Gen 3 - OFF')
	pushSeqCmd(dt, 'ELECTRICAL_GENERATOR_4', 0, 'Gen 4 - OFF')

	pushSeqCmd(dt, 'scriptSpeech', 'Shutdown complete.')
	return seq


###############################################################################
# CARP TEST  (auto Computed Air Release Point - WORK IN PROGRESS)
# ---------------------------------------------------------------------------
# Goal: drive the pilot CNI-MU to build/verify a CARP airdrop solution for a
# waypoint that the mission has designated. Built one page at a time.
#
# ACCESS PATH (from the manual + CNI page files):
#   The CARP INIT pages are reached from a CARP-type waypoint:
#     LEGS -> select the waypoint -> WAYPOINT DATA 1/2 -> R6 "MFP>" ->
#       (waypoint type CARP) -> CARP INIT 1/5
#   MFP>  = WAYPOINT DATA 1/2 / 2/2 R6.  It branches to CARP INIT ONLY if the
#   waypoint TYPE is already "CARP" (else WPT -> MISSIONS).  << OPEN QUESTION:
#   is the mission waypoint pre-typed CARP, or must we convert it via MISSIONS?
#
# CARP INIT LSK MAP (pilot CNI; each LSK spans two render rows: rows 1-2=L1,
# 3-4=L2, 5-6=L3, 7-8=L4, 9-10=L5, 11-12=L6; same for R1-R6). From the mod's
# CNI_MU/pages/carp_init_*.lua:
#
#   CARP INIT 1/5 (drop zone / geometry):
#     L1 LBL/IDENT (PI waypoint id)   R1 TOT (time on target)
#     L2 PI POSITION (lat/long)       R3 LE-PI (yd)
#     L3 LENGTH LE-TE (yd)            R4 TP DIST (NM)
#     L4 SD DIST (NM)                 R5 DZ ESC (NM)
#     L5 RUN IN CRS                   R6 CARP PROG>
#     L6 <back (MISSIONS/LEGS)
#
#   CARP INIT 2/5 (load):
#     L1 LOAD  (PER/CDS/HE/BDL-OTH)   R1 FUS STA (CDS/HE/BDL)
#     L2 STAGE (1/2)                  R2 RELEASE SYS (per load type)
#     L3 CHUTE/#                       R3 ELEM WT/QTY
#     L4 CAS                          R4 DROP PAYLD
#     L5 RACETRACK (ESC/L/R)          R5 CHUTE LIST>
#     L6 <back                        R6 CARP PROG>
#
#   CARP INIT 3/5 (weather):
#     L1 ALT W/V     L3 SFC W/V   L5 ALTIMETER SETTING (QNH/QFE) + R5 press val
#     R1 ALT TEMP    R3 SFC TEMP
#
#   CARP INIT 4/5 (altitude/elevation):
#     L1 DROP ALTITUDE ref (QNH/PA)   R1 DROP ALTITUDE value
#     L4 RQD CLNC HT                  R3 PI ELEVATION
#     L5 MIN DROP HT                  R4 OBSTR ELEV   R5 DZ ELEV
#
#   CARP INIT 5/5 = ballistics readout (display only, no entry).
#
# NO-INPUT-POPUP WORKAROUND: arbitrary values are typed into the CNI scratchpad
# with cni_type() (keyboard keys), then the target LSK is pressed to accept.
# Multi-toggle fields (LOAD, STAGE, RACETRACK, ALTIMETER SETTING, DROP ALT ref)
# are cycled by pressing their LSK N times.
###############################################################################

# --- CNI scratchpad keyboard helper -----------------------------------------
# Maps characters to the pilot CNI keyboard DCS-BIOS controls so the script can
# "type" any identifier/number into the scratchpad, then press an LSK to enter.
_CNI_KEY = {
	'0': 'PLT_CNI_KBD_0', '1': 'PLT_CNI_KBD_1', '2': 'PLT_CNI_KBD_2',
	'3': 'PLT_CNI_KBD_3', '4': 'PLT_CNI_KBD_4', '5': 'PLT_CNI_KBD_5',
	'6': 'PLT_CNI_KBD_6', '7': 'PLT_CNI_KBD_7', '8': 'PLT_CNI_KBD_8',
	'9': 'PLT_CNI_KBD_9', '.': 'PLT_CNI_KBD_DOT', '/': 'PLT_CNI_KBD_SLASH',
	'-': 'PLT_CNI_KBD_PLUSMINUS', '+': 'PLT_CNI_KBD_PLUSMINUS',
}
for _c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
	_CNI_KEY[_c] = f'PLT_CNI_KBD_{_c}'


def CarpProbe(config, vars):
	"""
	STAGE 1 CARGO/LOAD PROBE (read-only).

	The mod does NOT expose loaded-cargo (type / chute / weight / qty) as
	readable cockpit params -- that data lives in a compiled device and only
	surfaces on the CARP INIT 2/5 page, where the aircraft auto-fills:
	    LOAD class, CHUTE/#, ELEM WT/QTY, DROP PAYLD
	from whatever cargo is currently staged. We read those back off the pilot
	CNI display (DCS-BIOS indicator id 8) via the CARP_PROBE_A/B string exports.

	Because we read what the CNI shows, server-custom cargo weights come through
	automatically; vanilla weights are just the default case.

	HOW TO USE:
	  1. Load your cargo (e.g. 4x CDS BARRELS, G-12D) as normal.
	  2. On the pilot CNI, open CARP INIT page 2/5 (the LOAD/CHUTE/ELEM page).
	  3. Run this profile. It waits, then prints (and optionally speaks) the raw
	     CNI dump as "index=value;" pairs so we can read the exact strings and
	     their ordinal positions. Nothing in the cockpit is touched.
	"""
	seq = []

	def pushSeqCmd(dt, cmd, *args, **kwargs):
		if len(args):
			seq.append({'time': round(dt, 2), 'cmd': cmd, 'arg': args[0],
				'msg': args[1] if len(args) > 1 else ''})
		else:
			step = {'time': round(dt, 2), 'cmd': cmd}
			for key in kwargs:
				step[key] = kwargs[key]
			seq.append(step)

	delay = float(vars.get('Delay s', '5'))
	speak = (vars.get('Speak', 'No') == 'Yes')

	pushSeqCmd(0, '', '', 'CARP Cargo Probe (read-only). Be on CARP INIT page 2/5.')
	pushSeqCmd(0.5, 'scriptSpeech',
		'Carp cargo probe. Make sure carp init page 2 is showing.')
	pushSeqCmd(delay, '', '', f'Waited {delay:g}s - reading CNI now')

	# One-shot reads of the two probe strings. Print always; speak if requested.
	pushSeqCmd(0.5, 'scriptEcho', arg='C-130J/CARP_PROBE_A',
		msg='CNI dump elems 1-24:', speak=speak)
	pushSeqCmd(0.5, 'scriptEcho', arg='C-130J/CARP_PROBE_B',
		msg='CNI dump elems 25-55:', speak=speak)

	pushSeqCmd(0.5, 'scriptSpeech',
		'Probe complete. Check the DCS Automate window for the dump.')

	# ---------------------------------------------------------------------
	# What to send back after running this:
	#   the two "ECHO ... CARP_PROBE_A/B = ..." lines from the DCSAutoMate
	#   window. From those ordinals we replace the wide probes with four narrow
	#   per-field reads (LOAD class, CHUTE/#, ELEM WT/QTY, DROP PAYLD) and wire
	#   them into the CARP build as the dynamic cargo values.
	# ---------------------------------------------------------------------
	return seq


def _wind_vec_to_dirspeed(w):
	"""
	Convert a DCS wind VELOCITY vector to meteorological (FROM) direction + speed.

	DCS world frame: x = North, y = Up, z = East (m/s). The vector points the way
	the wind blows TO; meteorology reports where it comes FROM, so
	FROM = (blows-to + 180) mod 360.

	Returns (from_deg, speed_kt, blows_to_deg) or None.
	"""
	import math
	if not isinstance(w, dict):
		return None
	x = float(w.get('x', 0) or 0)   # North m/s
	z = float(w.get('z', 0) or 0)   # East  m/s
	speed_kt = round(math.hypot(x, z) * 1.94384)
	blows_to = round(math.degrees(math.atan2(z, x))) % 360
	from_deg = (blows_to + 180) % 360
	return (from_deg, speed_kt, blows_to)


def _wind_from_export(config, key='LoGetVectorWindVelocity'):
	"""
	Meteorological wind from the build-time export snapshot.
	key='LoGetVectorWindVelocity' = wind at the aircraft's altitude (ALT W/V);
	key='DAM_SurfaceWind'          = surface-layer wind below the aircraft (SFC W/V).
	Returns (from_deg, speed_kt, blows_to_deg) or None.
	"""
	data = (config or {}).get('DAMExportData', {}) or {}
	return _wind_vec_to_dirspeed(data.get(key))


def _runin_from_legs(config, wp):
	"""
	Read the inbound leg course to waypoint LL0<wp> from the ACT LEGS page,
	captured at build time in the CNI dump strings (CARP_PROBE_A/B = indication 8).

	On ACT LEGS each waypoint block renders as [course^, distNM, time, *LL0N, ...],
	so the inbound leg course sits 3 elements before the "*LL0N" name element
	(observed: 008->LL01, 012->LL02, 027->LL03). That leg course IS the run-in.

	Returns the course as an int (0..359) or None if not found (e.g. not on the
	ACT LEGS page when Run was clicked, or the waypoint isn't on the shown page).
	"""
	data = (config or {}).get('DCSBIOSData', {}) or {}

	# Preferred: the compact "LL0N=deg;" map from CARP_LEGS_CRS (no truncation,
	# all waypoints).
	crs = data.get('C-130J/CARP_LEGS_CRS')
	if isinstance(crs, str) and crs.strip():
		for pair in crs.split(';'):
			if '=' in pair:
				name, deg = pair.split('=', 1)
				if name.strip() == f'LL0{wp}':
					digits = ''.join(c for c in deg if c.isdigit())
					if digits:
						return int(digits) % 360

	# Fallback: parse the raw CNI ordinal dump (CARP_PROBE_A/B). The inbound leg
	# course sits 3 elements before the "*LL0N" name element.
	dump = ''
	for k in ('C-130J/CARP_PROBE_A', 'C-130J/CARP_PROBE_B'):
		v = data.get(k)
		if isinstance(v, str):
			dump += v
	idxval = {}
	for pair in dump.split(';'):
		if '=' in pair:
			ks, vs = pair.split('=', 1)
			try:
				idxval[int(ks)] = vs
			except ValueError:
				pass
	target = f'*LL0{wp}'
	for idx, val in idxval.items():
		if val.strip() == target:
			course = idxval.get(idx - 3, '')          # course is 3 elements before name
			digits = ''.join(c for c in course if c.isdigit())
			if digits:
				return int(digits) % 360
	return None


def _elev_from_legs(config, wp):
	"""
	Waypoint ground ELEVATION (ft) for LL0<wp>, read from the ACT LEGS page.

	On ACT LEGS each waypoint carries a "----/NNNNNA" field whose digits before the
	trailing "A" are the elevation in feet ASL (set per waypoint by TheWay). The
	module exports the compact map "LL01=1;LL02=568;LL03=1552;" in CARP_LEGS_ELEV,
	captured in the same build snapshot as the run-in course (both come from ACT
	LEGS). We just read the drop waypoint's entry.

	Returns the elevation as an int, or None if not present (e.g. not on ACT LEGS at
	build, or that waypoint has no elevation). Callers fall back to the dropdown.
	"""
	data = (config or {}).get('DCSBIOSData', {}) or {}
	raw = data.get('C-130J/CARP_LEGS_ELEV')
	if not isinstance(raw, str) or not raw.strip():
		return None
	for pair in raw.split(';'):
		if '=' in pair:
			name, val = pair.split('=', 1)
			if name.strip() == f'LL0{wp}':
				val = val.strip()
				neg = val.startswith('-')
				digits = ''.join(c for c in val if c.isdigit())
				if digits:
					return -int(digits) if neg else int(digits)
	return None


def _bundle_stations(first, spacing, bundles, lo=345, hi=1005):
	"""
	Fuselage stations for a stick of <bundles> CDS bundles.

	First Station is the AFTMOST (largest) station: bundle 1 sits there and the
	stick steps FORWARD (down) by Spacing -- first, first-spacing, first-2*spacing,
	... No station can exceed the aft bay limit (hi=1005); any that would fall
	forward of the bay start (lo=345) is dropped. Returns the station list, aftmost
	first (so max() == First Station == the FUS STA reference).
	"""
	first = min(int(first), hi)          # can't go higher than the aft limit
	out = []
	for i in range(int(bundles)):
		s = first - i * int(spacing)
		if s < lo or s > hi:
			break
		out.append(s)
	return out


def WindCheck(config, vars):
	"""
	Report the export wind as computed FROM-direction + speed, to validate the
	vector->wind conversion (and the FROM-vs-blows-to convention) against a
	known mission wind before wiring it into the CARP INIT 3/5 fields.
	"""
	seq = []

	def pushSeqCmd(dt, cmd, *args, **kwargs):
		if len(args):
			seq.append({'time': round(dt, 2), 'cmd': cmd, 'arg': args[0],
				'msg': args[1] if len(args) > 1 else ''})
		else:
			step = {'time': round(dt, 2), 'cmd': cmd}
			for key_ in kwargs:
				step[key_] = kwargs[key_]
			seq.append(step)

	wind = _wind_from_export(config)
	if wind is None:
		msg = 'No wind data in export snapshot. Is the export flowing?'
	else:
		fdir, spd, bto = wind
		msg = (f'Export wind: FROM {fdir:03d} deg at {spd} kt '
			f'(blows to {bto:03d}). CARP entry would be {fdir:03d}/{spd:02d}.')
	pushSeqCmd(0, '', '', msg)
	pushSeqCmd(0.5, 'scriptSpeech', msg)
	return seq


def ExportDump(config, vars):
	"""
	Dump all data from the DCSAutoMate LoGet* export (DCSAutoMateExport.lua) via
	the scriptExportDump command, to survey what's available for CARP automation
	(ownship lat/long from LoGetSelfData, altitudes, speeds, payload, mech state,
	and -- if uncommented in the .lua -- winds and atmospheric pressure).

	Requires DCSAutoMateExport.lua wired into Export.lua and a mission running.
	The receiver updates ~1 Hz, so give it a couple seconds first.
	"""
	seq = []

	def pushSeqCmd(dt, cmd, *args, **kwargs):
		if len(args):
			seq.append({'time': round(dt, 2), 'cmd': cmd, 'arg': args[0],
				'msg': args[1] if len(args) > 1 else ''})
		else:
			step = {'time': round(dt, 2), 'cmd': cmd}
			for key_ in kwargs:
				step[key_] = kwargs[key_]
			seq.append(step)

	delay = float(vars.get('Delay s', '2'))
	filt = vars.get('Filter', '(all)')
	filt = '' if filt in ('(all)', '', None) else filt

	pushSeqCmd(0, '', '', 'Export Dump: survey of DCSAutoMate LoGet* export data')
	pushSeqCmd(0.5, 'scriptSpeech', 'Dumping export data.')
	pushSeqCmd(delay, '', '', f'Waited {delay:g}s for export data to arrive')
	pushSeqCmd(0.5, 'scriptExportDump', msg='survey', filter=filt)
	pushSeqCmd(0.5, 'scriptSpeech',
		'Export dump complete. Check the DCS Automate window.')
	return seq


def CarpPayload(config, vars):
	"""
	Drive the WT+BAL PAYLOAD entry the sim requires before a CARP.

	The game does NOT transfer loaded cargo to the avionics -- the crew types
	each bundle's weight + bay station on the PAYLOAD page. A DOUBLE SLASH
	between weight and station marks it as an AIRDROP payload (manual p.324),
	which the page redraws with an inverse slash.

	Nav path: MC INDX key -> L3 (WT+BAL) -> L4 (PAYLOAD).
	Fill order of the 10 PAYLOAD slots: L1..L5 then R1..R5.

	Bundles are laid out from First Station, stepping by Spacing. Fuselage
	stations run 345..1005; entries past 1005 are skipped. NOTE: this even-
	spacing model doesn't yet cover custom / two-per-row layouts (two pallets
	sharing one station) -- that's a later enhancement.
	"""
	seq = []

	def pushSeqCmd(dt, cmd, *args, **kwargs):
		if len(args):
			seq.append({'time': round(dt, 2), 'cmd': cmd, 'arg': args[0],
				'msg': args[1] if len(args) > 1 else ''})
		else:
			step = {'time': round(dt, 2), 'cmd': cmd}
			for key_ in kwargs:
				step[key_] = kwargs[key_]
			seq.append(step)

	def key(cmd, msg=''):
		# CNI function/mode key press+release.
		pushSeqCmd(0.5, cmd, 1, msg)
		pushSeqCmd(0.2, cmd, 0)

	def lsk(k, msg='', dt=0.25, rel=0.1):
		pushSeqCmd(dt, f'PLT_CNI_LSK_{k}', 1, msg)
		pushSeqCmd(rel, f'PLT_CNI_LSK_{k}', 0)

	def cni_type(text, msg='', dt=0.09, rel=0.05):
		if msg:
			pushSeqCmd(0.3, '', '', msg)
		for ch in str(text).upper():
			k = _CNI_KEY.get(ch)
			if k is None:
				continue
			pushSeqCmd(dt, k, 1)
			pushSeqCmd(rel, k, 0)

	bundles = int(vars.get('Bundles', '4'))
	weight  = str(vars.get('Weight lb ea', '882'))
	first   = int(vars.get('First Station', '1005'))
	spacing = int(vars.get('Spacing in', '60'))
	sep     = '//' if vars.get('Airdrop', 'Yes') == 'Yes' else '/'

	slots = ['L1', 'L2', 'L3', 'L4', 'L5', 'R1', 'R2', 'R3', 'R4', 'R5']
	bundles = max(1, min(bundles, len(slots)))

	pushSeqCmd(0, '', '', f'CARP Payload Entry: {bundles} x {weight}lb from '
		f'stn {first} step {spacing}, {"airdrop //" if sep == "//" else "normal /"}')
	pushSeqCmd(1.0, 'scriptSpeech',
		f'Entering {bundles} payload bundles at {weight} pounds.')

	# --- Navigate to PAYLOAD: MC INDX -> WT+BAL (L3) -> PAYLOAD (L4) ---
	key('PLT_CNI_MC_INDX', 'MC INDX key -> MSN CMPTR INDEX')
	pushSeqCmd(0.8, '', '', 'Settle on MSN CMPTR INDEX')
	lsk('L3', 'L3 -> WT + BAL')
	pushSeqCmd(0.8, '', '', 'Settle on WT + BAL')
	lsk('L4', 'L4 -> PAYLOAD')
	pushSeqCmd(1.0, '', '', 'Settle on PAYLOAD page')

	# --- Type each bundle: "<weight>//<station>" then the next LSK ---
	# No CLR needed: pressing the LSK to apply the entry auto-clears the
	# scratchpad on the PAYLOAD page (confirmed in-sim).
	# First Station is the AFTMOST (largest) station; the stick steps FORWARD
	# (down) by Spacing so every bundle is entered for weight & balance.
	stations = _bundle_stations(first, spacing, bundles)
	if len(stations) < bundles:
		pushSeqCmd(0.3, 'scriptSpeech',
			f'Only {len(stations)} of {bundles} bundles fit forward of station '
			f'{first}. Lower the First Station or Spacing.')
	for i, station in enumerate(stations):
		entry = f'{weight}{sep}{station}'
		cni_type(entry, f'Bundle {i + 1}: {entry} at {slots[i]}')
		lsk(slots[i], f'Enter bundle {i + 1} at {slots[i]}')

	pushSeqCmd(0.5, 'scriptSpeech',
		'Payload entry complete. Verify T O payload and arm total.')

	# ---------------------------------------------------------------------
	# NEXT STEP (user-confirmed: ELEM WT/QTY does NOT auto-pull from PAYLOAD).
	# On CARP INIT 2/5 (manual pp.298-299):
	#   L1 = cycle load class to CDS   L2 = STAGE
	#   L3 = CHUTE/#  (type or CHUTE LIST> downselect, e.g. G-12D/1)
	#   R1 = FUS STA (first element station)
	#   R2 = RELEASE SYS (TOW/EXTR for CDS)
	#   R3 = ELEM WT/QTY -> type "<wt>/<qty>" e.g. 882/4 -> "882LB/4"
	#   R4 = DROP PAYLD (auto-computes from R3; manual override allowed)
	# ---------------------------------------------------------------------
	return seq


def CarpTest(config, vars):
	"""
	Full CARP airdrop flow, three phases in one run:
	  PHASE 1  PAYLOAD (WT+BAL)  -- prerequisite; type each bundle weight//station
	  PHASE 2  PI setup          -- copy the drop waypoint, paste into CARP INIT 1/5
	  PHASE 3  CARP INIT 2/5 load-- load class, FUS STA, ELEM WT/QTY, release, chute

	Backed by the DCS C-130J manual (pp.296-324) and a CARP walkthrough:
	  - PAYLOAD: "weight//station", DOUBLE SLASH = airdrop (inverse-slash on screen)
	  - ELEM WT/QTY = "<wt>/<count>" e.g. 882/4 for four 882 lb containers
	  - Chute: CHUTE LIST -> downselect chute -> back -> L3 (number auto-generates 1)
	  - DROP PAYLD (R4) auto-computes from ELEM WT/QTY
	All CNI keys are press+release. LSK-apply auto-clears the scratchpad (as on
	the PAYLOAD page), so no CLR between typed fields.

	Confirmed in-sim: fresh CARP defaults LOAD=CDS and RELEASE=CRS, so both are
	0 presses at defaults (CDS airdrops always use CRS); chute L3 number
	auto-generates. VERIFY only for non-default picks:
	  * CHUTE LIST positions assumed G-12D=L1, G-12E=L2 (G-12E untested).
	"""
	seq = []

	# Global speed factor for the whole CARP flow: 0.5 = 50% faster across the
	# board (every step -- key presses, LSK applies, page settles -- routes through
	# pushSeqCmd). A small floor keeps DCS-BIOS presses long enough to register.
	CARP_SPEED = 0.5
	def pushSeqCmd(dt, cmd, *args, **kwargs):
		dt = dt * CARP_SPEED
		if dt and dt < 0.05:
			dt = 0.05
		if len(args):
			seq.append({'time': round(dt, 2), 'cmd': cmd, 'arg': args[0],
				'msg': args[1] if len(args) > 1 else ''})
		else:
			step = {'time': round(dt, 2), 'cmd': cmd}
			for key_ in kwargs:
				step[key_] = kwargs[key_]
			seq.append(step)

	def fkey(cmd, msg=''):
		# CNI function/mode key press+release (LEGS, MSN, MC INDX, NEXT PAGE).
		pushSeqCmd(0.6, cmd, 1, msg)
		pushSeqCmd(0.25, cmd, 0)

	def lsk(k, msg='', dt=0.5, rel=0.2):
		pushSeqCmd(dt, f'PLT_CNI_LSK_{k}', 1, msg)
		pushSeqCmd(rel, f'PLT_CNI_LSK_{k}', 0)

	def cni_type(text, msg='', dt=0.22, rel=0.12):
		if msg:
			pushSeqCmd(0.3, '', '', msg)
		for ch in str(text).upper():
			k = _CNI_KEY.get(ch)
			if k is None:
				continue
			pushSeqCmd(dt, k, 1)
			pushSeqCmd(rel, k, 0)

	def cycle(k, n, msg=''):
		# Press a multi-toggle LSK n times to advance the selection.
		for i in range(n):
			pushSeqCmd(0.6, f'PLT_CNI_LSK_{k}', 1, (msg if i == 0 else ''))
			pushSeqCmd(0.25, f'PLT_CNI_LSK_{k}', 0)

	def execkey(msg='EXEC - commit/save this CARP page'):
		# Press EXEC to save the current CARP page's entries before advancing.
		# Each page is EXEC'd once it's fully filled (page 1 complete -> EXEC ->
		# page 2 ...), so nothing is lost when NEXT PAGE changes the display.
		pushSeqCmd(0.6, 'PLT_CNI_EXEC', 1, msg)
		pushSeqCmd(0.3, 'PLT_CNI_EXEC', 0)
		pushSeqCmd(0.6, '', '', 'Settle after EXEC')

	# --- vars ---
	carp_wp = vars.get('CARP Waypoint', '1')
	pi_ident = f'LL0{carp_wp}'                       # TheWay "Waypoint N" -> LL0N
	bundles = max(1, min(int(vars.get('Bundles', '4')), 10))
	weight  = str(vars.get('Weight lb ea', '882'))
	first   = int(vars.get('First Station', '1005'))
	spacing = int(vars.get('Spacing in', '60'))
	# Bundle stations: First Station (aftmost/largest) stepping FORWARD by Spacing.
	stations = _bundle_stations(first, spacing, bundles)
	load    = vars.get('Load', 'CDS')
	rel     = vars.get('Release Sys', 'CRS')
	chute   = vars.get('Chute', 'G-12D')
	cas     = str(vars.get('CAS', '140'))
	winds   = vars.get('Winds', 'FROM')             # FROM / BLOWS-TO / OFF
	sfc_tmp = int(vars.get('Surface Temp C', '20')) # surface temp from briefing
	drop_ft = int(vars.get('Drop Alt ft', '1000'))  # planned drop altitude (ft)
	# CARP INIT 1/5 geometry (drop-zone dimensions).
	geom    = vars.get('Geometry', 'ON')
	le_te   = vars.get('LE-TE yd', '1000')
	le_pi   = vars.get('LE-PI yd', '100')
	sd_dist = vars.get('SD Dist NM', '6')
	tp_dist = vars.get('TP Dist NM', '10')
	dz_esc  = vars.get('DZ ESC NM', '0.5')
	# CARP INIT 4/5 drop altitude + elevations.
	drop_ref = vars.get('Drop Alt Ref', 'QNH')      # QNH / PA (L1 toggle)
	# PI ELEV comes straight from the selected waypoint's ACT LEGS "A" (ASL) height,
	# set per waypoint by TheWay -- no manual dropdown. Falls back to 0 ft only if
	# that waypoint has no elevation / the CNI wasn't on ACT LEGS at Run.
	# The CARP 4/5 page enforces PI <= OBSTR <= DZ, so we step each up 10 ft:
	#   OBSTR ELEV = PI + 10 ,  DZ ELEV = OBSTR + 10 (= PI + 20),
	# and they MUST be entered PI-first, then OBSTR, then DZ (see phase 5).
	pi_elev_n    = _elev_from_legs(config, carp_wp)
	pi_elev_n    = pi_elev_n if pi_elev_n is not None else 0
	obstr_elev_n = pi_elev_n + 10
	dz_elev_n    = obstr_elev_n + 10
	pi_elev    = str(pi_elev_n)
	obstr_elev = str(obstr_elev_n)
	dz_elev    = str(dz_elev_n)
	min_dh   = vars.get('Min Drop Ht ft', '600')
	qty     = bundles                                # elements = bundle count

	LOAD_OPTS = ['PER', 'CDS', 'HE', 'BDL-OTH']
	# Confirmed in-sim: a fresh CARP defaults to CDS, so cycle L1 relative to
	# CDS (CDS=0 presses, HE=1, BDL-OTH=2, PER=3). The toggle wraps.
	LOAD_DEFAULT_IDX = LOAD_OPTS.index('CDS')
	load_presses = ((LOAD_OPTS.index(load) - LOAD_DEFAULT_IDX) % len(LOAD_OPTS)
		) if load in LOAD_OPTS else 0
	# Release options are load-dependent (from the mod's carp_init_2 page).
	rel_opts = {'CDS': ['NA', 'CRS', 'TOW'], 'HE': ['EXTR', 'TOW']}.get(load,
		['NA', 'CRS', 'TOW'])
	# CDS release toggle defaults to CRS (confirmed in-sim: CRS = 0 presses).
	rel_default = 'CRS' if 'CRS' in rel_opts else rel_opts[0]
	rel_default_idx = rel_opts.index(rel_default)
	rel_presses = ((rel_opts.index(rel) - rel_default_idx) % len(rel_opts)
		) if rel in rel_opts else 0
	chute_lsk = {'G-12D': 'L1', 'G-12E': 'L2'}.get(chute, 'L1')
	slots = ['L1', 'L2', 'L3', 'L4', 'L5', 'R1', 'R2', 'R3', 'R4', 'R5']

	pushSeqCmd(0, '', '', 'C-130J CARP flow: PAYLOAD -> PI -> CARP INIT 2/5 load')

	# =====================================================================
	# PHASE 1 - PAYLOAD (WT+BAL): MC INDX -> L3 (WT+BAL) -> L4 (PAYLOAD)
	# Each bundle: "<weight>//<station>" (// = airdrop) applied to the next LSK.
	# =====================================================================
	pushSeqCmd(1.0, 'scriptSpeech', f'Phase one. Loading {bundles} payload bundles.')
	fkey('PLT_CNI_MC_INDX', 'MC INDX -> MSN CMPTR INDEX')
	pushSeqCmd(0.8, '', '', 'Settle on MSN CMPTR INDEX')
	lsk('L3', 'L3 -> WT + BAL')
	pushSeqCmd(0.8, '', '', 'Settle on WT + BAL')
	lsk('L4', 'L4 -> PAYLOAD')
	pushSeqCmd(1.0, '', '', 'Settle on PAYLOAD')
	# First Station is the AFTMOST (largest) station; the stick steps FORWARD
	# (down) by Spacing so ALL bundles get entered for weight & balance.
	if len(stations) < bundles:
		pushSeqCmd(0.3, 'scriptSpeech',
			f'Only {len(stations)} of {bundles} bundles fit forward of station '
			f'{first}. Lower the First Station or Spacing.')
	for i, station in enumerate(stations):
		# Fast cadence for the (simple numeric) payload entry.
		cni_type(f'{weight}//{station}',
			f'Bundle {i + 1}: {weight}//{station} at {slots[i]}', dt=0.09, rel=0.05)
		lsk(slots[i], f'Apply bundle {i + 1} at {slots[i]}', dt=0.25, rel=0.1)

	# =====================================================================
	# PHASE 2 - PI setup (user-confirmed flow). DOWNSELECT the drop waypoint with
	# its RIGHT LSK on ACT LEGS -> opens that waypoint's WAYPOINT DATA page; then
	# MFP> (R6) -> MISSIONS -> CARP 1 INIT> (R2) -> CARP INIT 1/5. Entering CARP
	# INIT through the waypoint's data page this way ties the PI to that waypoint
	# natively -- no scratchpad copy/paste (the earlier LEFT-LSK copy was wrong).
	#   ACT LEGS: waypoint N is on the RIGHT LSK R{N} (LL02 = R2).
	#   WAYPOINT DATA: MFP> = R6.  MISSIONS: CARP 1 INIT> = R2.
	# =====================================================================
	pushSeqCmd(1.0, 'scriptSpeech', f'Phase two. Point of impact from waypoint {carp_wp}.')
	fkey('PLT_CNI_LEGS', 'LEGS -> ACT LEGS')
	pushSeqCmd(1.0, '', '', 'Settle on ACT LEGS')
	# Downselect the drop waypoint via its RIGHT LSK -> its WAYPOINT DATA page.
	lsk(f'R{carp_wp}', f'Select {pi_ident} via R{carp_wp} -> WAYPOINT DATA')
	pushSeqCmd(1.0, '', '', 'Settle on WAYPOINT DATA')
	# MFP> (R6) -> MISSIONS.
	lsk('R6', 'MFP> (R6) -> MISSIONS')
	pushSeqCmd(1.0, '', '', 'Settle on MISSIONS')
	# CARP 1 INIT> (R2) -> CARP INIT 1/5, PI already tied to the selected waypoint.
	lsk('R2', 'CARP 1 INIT> (R2) -> CARP INIT 1/5')
	pushSeqCmd(1.0, '', '', 'Settle on CARP INIT 1/5')

	# --- 2b. RUN IN CRS (L5) from the ACT LEGS inbound leg course ---
	# Read at build time from the CNI dump (CARP_PROBE_A/B). Requires being on the
	# ACT LEGS page when Run is clicked; otherwise it's skipped gracefully.
	# Still on CARP INIT 1/5 here (before the NEXT PAGE to 2/5).
	runin = _runin_from_legs(config, carp_wp)
	if runin is not None:
		cni_type(f'{runin:03d}', f'RUN IN CRS {runin:03d} (LEGS leg to LL0{carp_wp})')
		lsk('L5', 'Apply RUN IN CRS at L5')
		pushSeqCmd(0.3, 'scriptSpeech', f'Run in course {runin:03d} from the leg.')
	else:
		pushSeqCmd(0.3, 'scriptSpeech',
			'Run in course not read. Be on ACT LEGS when you run this.')

	# --- 2c. CARP INIT 1/5 geometry (drop-zone dimensions). Still on 1/5. ---
	# L3 LE-TE (yd), L4 SD DIST (NM), R3 LE-PI (yd), R4 TP DIST (NM),
	# R5 DZ ESC (NM). The boxed mandatory fields the CARP needs to compute.
	if geom == 'ON':
		# TP DIST / SD DIST come from the dropdowns. NOTE: do NOT shrink TP DIST to
		# the tiny WP1-leg distance -- that collapses the CARP's own run-in/pattern
		# generation (the AUTO CARP). Alignment to the route comes from RUN IN CRS
		# (set above from the LEGS leg course), which points the run-in down the
		# WP1->drop bearing without breaking the auto pattern.
		pushSeqCmd(0.5, 'scriptSpeech', 'Setting drop zone geometry.')
		cni_type(le_te, f'LE-TE {le_te} yd')
		lsk('L3', 'Apply LE-TE at L3')
		cni_type(sd_dist, f'SD DIST {sd_dist} NM')
		lsk('L4', 'Apply SD DIST at L4')
		cni_type(tp_dist, f'TP DIST {tp_dist} NM')
		lsk('R4', 'Apply TP DIST at R4')
		cni_type(dz_esc, f'DZ ESC {dz_esc} NM')
		lsk('R5', 'Apply DZ ESC at R5')
		# LE-PI (R3) LAST, with a cleared scratchpad + settle. It was not landing
		# when entered mid-block (a later field entry appears to clear it), so it
		# goes after the others with a clean scratchpad so the value sticks.
		for i in range(3):
			pushSeqCmd(0.12, 'PLT_CNI_KBD_CLR', 1, ('Clear scratchpad before LE-PI' if i == 0 else ''))
			pushSeqCmd(0.08, 'PLT_CNI_KBD_CLR', 0)
		pushSeqCmd(0.5, '', '', 'Settle before LE-PI entry')
		cni_type(le_pi, f'LE-PI {le_pi} yd')
		lsk('R3', 'Apply LE-PI at R3')

	# =====================================================================
	# PHASE 3 - CARP INIT 2/5 load. NEXT PAGE from 1/5, then set the load.
	#   L1 = load class (cycle)   R1 = FUS STA (first station)
	#   R3 = ELEM WT/QTY (wt/cnt) R2 = RELEASE SYS (cycle)   L4 = CAS
	#   R5 -> CHUTE LIST -> chute LSK -> L6 back -> L3 (number auto-gen)
	#   R4 = DROP PAYLD auto-computes.
	# =====================================================================
	# CARP INIT 1/5 complete -> EXEC to save it, then advance to 2/5.
	execkey('EXEC - save CARP INIT 1/5 (PI / run-in / geometry)')
	pushSeqCmd(1.0, 'scriptSpeech', 'Page one saved. Phase three. Setting airdrop load.')
	fkey('PLT_CNI_NEXT_PAGE', 'NEXT PAGE -> CARP INIT 2/5')
	pushSeqCmd(1.0, '', '', 'Settle on CARP INIT 2/5')

	# L1: load class (cycle from CDS default; CDS = 0 presses).
	if load_presses > 0:
		cycle('L1', load_presses,
			f'L1 x{load_presses} -> {load} (from CDS default)')
	# R1: FUS STA = the LARGEST (aftmost) fuselage station = the First Station,
	# since the stick steps forward (down) from it. Bundles extract out the ramp
	# aft-first, so the first to release is the highest station number. Uses the
	# same station list built for the payload (max == First Station).
	fus_sta = max(stations) if stations else first
	cni_type(str(fus_sta),
		f'FUS STA {fus_sta} (aftmost of {len(stations)} bundle stations)')
	lsk('R1', 'Apply FUS STA at R1')
	# R3: ELEM WT/QTY = weight/count.
	cni_type(f'{weight}/{qty}', f'ELEM WT/QTY {weight}/{qty}')
	lsk('R3', 'Apply ELEM WT/QTY at R3')
	# R2: RELEASE SYS (VERIFY: assumes index-0 default of {rel_opts}).
	if rel_presses > 0:
		cycle('R2', rel_presses,
			f'R2 x{rel_presses} -> {rel} from {rel_opts} [VERIFY]')
	# L4: CAS (drop speed).
	cni_type(cas, f'CAS {cas}')
	lsk('L4', 'Apply CAS at L4')
	# Chute: CHUTE LIST (R5) -> downselect -> back (L6) -> L3 (# auto-generates).
	lsk('R5', 'R5 -> CHUTE LIST')
	pushSeqCmd(1.0, '', '', 'Settle on CHUTE LIST')
	lsk(chute_lsk, f'Downselect {chute} (assumed {chute_lsk}) [VERIFY]')
	lsk('L6', 'L6 -> back to CARP INIT 2/5')
	pushSeqCmd(0.8, '', '', 'Settle on CARP INIT 2/5')
	lsk('L3', f'Apply CHUTE {chute} at L3 (# auto-generates)')

	pushSeqCmd(1.0, 'scriptSpeech',
		'CARP load set. Verify chute, element weight, and drop payload.')

	# =====================================================================
	# PHASE 4 - CARP INIT 3/5 winds + temperature.
	# Winds: ALT W/V (L1) from LoGetVectorWindVelocity (aircraft-altitude wind --
	# run at drop altitude); SFC W/V (L3) from DAM_SurfaceWind (true surface wind).
	# Direction per 'Winds' var: FROM (met, default) or BLOWS-TO.
	# Temperature: not in the export, so ALT TEMP (R1) = briefed Surface Temp minus
	# ISA lapse (~2 C / 1000 ft) for the drop altitude (manual: R1 = drop-alt temp).
	# SFC TEMP (R3) auto-populates, so we leave it.
	# =====================================================================
	alt_wind = _wind_from_export(config)                        # wind at aircraft alt
	sfc_wind = _wind_from_export(config, 'DAM_SurfaceWind') or alt_wind
	do_winds = (winds != 'OFF') and (alt_wind is not None)
	# ALT TEMP by ISA lapse rate (2 C / 1000 ft) from the briefed surface temp.
	alt_temp = sfc_tmp - round(2 * drop_ft / 1000.0)

	def _wfmt(wnd):
		fdir, spd, bto = wnd
		wdir = fdir if winds == 'FROM' else bto
		return f'{wdir:03d}/{spd:02d}', wdir, spd

	# CARP INIT 2/5 complete -> EXEC to save it, then advance to 3/5.
	execkey('EXEC - save CARP INIT 2/5 (load)')
	pushSeqCmd(1.0, 'scriptSpeech',
		f'Page two saved. Phase four. Winds and altitude temperature {alt_temp}.')
	fkey('PLT_CNI_NEXT_PAGE', 'NEXT PAGE -> CARP INIT 3/5')
	pushSeqCmd(1.0, '', '', 'Settle on CARP INIT 3/5')

	# Winds (skip if OFF or no export data).
	if do_winds:
		alt_str, adir, aspd = _wfmt(alt_wind)
		sfc_str, sdir, sspd = _wfmt(sfc_wind)
		cni_type(alt_str, f'ALT W/V {alt_str} ({winds}) at L1')
		lsk('L1', 'Apply ALT W/V at L1')
		cni_type(sfc_str, f'SFC W/V {sfc_str} ({winds}) at L3')
		lsk('L3', 'Apply SFC W/V at L3')
	elif winds != 'OFF':
		pushSeqCmd(0.3, 'scriptSpeech', 'No wind data in export; winds skipped.')

	# ALT TEMP (R1). Negative temps use the +/- key (cni_type maps '-').
	cni_type(str(alt_temp),
		f'ALT TEMP {alt_temp}C (sfc {sfc_tmp} - lapse @ {drop_ft}ft) at R1')
	lsk('R1', 'Apply ALT TEMP at R1')
	pushSeqCmd(0.5, 'scriptSpeech',
		'Winds and altitude temperature set. Verify page 3.')

	# =====================================================================
	# PHASE 5 - CARP INIT 4/5 drop altitude + elevations. NEXT PAGE from 3/5.
	# Page layout (from the mod's carp_init_4.lua): L1 DROP ALT ref (QNH/PA),
	# R1 DROP ALTITUDE, R3 PI ELEVATION, R4 OBSTR ELEV, R5 DZ ELEV, L5 MIN DROP HT.
	# ORDER MATTERS: PI ELEVATION must be entered FIRST, then OBSTR (PI+10), then
	# DZ (OBSTR+10) -- the page enforces PI <= OBSTR <= DZ, so an out-of-order or
	# equal value gets rejected/clamped. DROP ALT + MIN DROP HT go after.
	# =====================================================================
	# CARP INIT 3/5 complete -> EXEC to save it, then advance to 4/5.
	execkey('EXEC - save CARP INIT 3/5 (winds / temp)')
	pushSeqCmd(1.0, 'scriptSpeech', 'Page three saved. Phase five. Drop altitude and elevations.')
	fkey('PLT_CNI_NEXT_PAGE', 'NEXT PAGE -> CARP INIT 4/5')
	pushSeqCmd(1.0, '', '', 'Settle on CARP INIT 4/5')
	# L1: DROP ALT ref toggle (assume QNH default; PA = 1 press) [VERIFY default].
	if drop_ref == 'PA':
		cycle('L1', 1, 'L1 -> PA (from QNH default) [VERIFY]')
	# --- Elevations first, in ascending order PI -> OBSTR -> DZ ---
	# R3: PI ELEVATION (ft) = waypoint LEGS height. Entered first.
	cni_type(pi_elev, f'PI ELEVATION {pi_elev} ft (from LEGS)')
	lsk('R3', 'Apply PI ELEVATION at R3')
	# R4: OBSTR ELEV (ft) = PI + 10.
	cni_type(obstr_elev, f'OBSTR ELEV {obstr_elev} ft (PI + 10)')
	lsk('R4', 'Apply OBSTR ELEV at R4')
	# R5: DZ ELEVATION (ft) = OBSTR + 10 (= PI + 20).
	cni_type(dz_elev, f'DZ ELEVATION {dz_elev} ft (OBSTR + 10)')
	lsk('R5', 'Apply DZ ELEVATION at R5')
	# --- Then drop altitude + min drop height ---
	# R1: DROP ALTITUDE (ft) = the planned drop altitude.
	cni_type(str(drop_ft), f'DROP ALTITUDE {drop_ft} ft')
	lsk('R1', 'Apply DROP ALTITUDE at R1')
	# L5: MIN DROP HT (ft).
	cni_type(min_dh, f'MIN DROP HT {min_dh} ft')
	lsk('L5', 'Apply MIN DROP HT at L5')
	pushSeqCmd(0.5, 'scriptSpeech', 'Drop altitude and elevations set.')

	# =====================================================================
	# PHASE 6 - Final EXEC to save CARP INIT 4/5 (the last page). Every page is
	# EXEC'd once complete, so this commits page 4 and finishes the profile.
	# =====================================================================
	execkey('EXEC - save CARP INIT 4/5 (drop alt / elevations)')
	pushSeqCmd(0.5, 'scriptSpeech', 'Page four saved. CARP setup complete.')

	# ---------------------------------------------------------------------
	# NOTES / manual entries that remain:
	#  - CARP INIT 3/5 altimeter (QNH) - not exported, enter manually.
	#  - CARP INIT 4/5 RQD CLNC HT / OBSTR ELEV - only if there's an obstacle.
	#  - VERIFY toggle defaults: L1 load (CDS ok), R2 release (CRS ok), 4/5 L1
	#    drop-alt-ref default, and CHUTE LIST positions for G-12E.
	# ---------------------------------------------------------------------
	return seq

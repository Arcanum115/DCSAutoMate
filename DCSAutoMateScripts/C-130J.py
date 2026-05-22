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
				'name': 'Test: Engine Switch Click',
				'function': 'TestEngineSwitches',
				'vars': {
					'Direction': ['1', '0'],
				},
			},
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
	pushSeqCmd(dt, 'PROP_SYNC', 1, 'Prop sync - ON')

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
	pushSeqCmd(dt, 'scriptSpeech', 'Applying power.')
	pushSeqCmd(dt, 'ELECTRICAL_BATTERY', 1, 'BATTERY - ON')
	pushSeqCmd(2.0, 'scriptSpeech', 'Battery on.')

	pushSeqCmd(dt, 'PLT_CC_LIGHTING_MASTER_DISPLAY_BRIGHTNESS',  int16(0.85))
	pushSeqCmd(dt, 'CPLT_CC_LIGHTING_MASTER_DISPLAY_BRIGHTNESS', int16(0.85))

	# --- External Power (optional, electrical only) ---
	# EXT PWR provides electrical supply. APU is still needed for bleed air
	# during engine start, so we always run the APU sequence below regardless.
	if vars.get('External Power') == 'Yes':
		pushSeqCmd(dt, 'ELECTRICAL_EXT_POWER_APU', 0, 'EXT PWR/APU - EXT PWR')
		pushSeqCmd(2.0, 'scriptSpeech', 'External power applied.')

	# --- APU Start (always run: APU bleed air is required for engine start) ---
	pushSeqCmd(dt, 'scriptSpeech', 'Starting A P U.')
	# APU control switch is spring-loaded out of START. Procedure:
	#   1) Drive switch to START (value 2)
	#   2) Hold ~2s for the start sequence to engage
	#   3) Release to RUN (value 1)
	#   4) Wait on APU_NG telemetry until it reaches operating RPM
	pushSeqCmd(dt, 'APU_SWITCH', 2, 'APU switch - START')
	pushSeqCmd(2.0, 'APU_SWITCH', 1, 'APU switch - RUN (release from spring)')

	# Wait for APU to reach full operating RPM (100%)
	pushSeqCmd(dt, 'scriptCockpitState',
		control='C-130J/APU_NG', value=100, condition='>=', duration=2)
	pushSeqCmd(dt, 'scriptSpeech', 'A P U at 100 percent.')
	# MC clear after APU online
	pushSeqCmd(dt, 'PLT_MASTER_CAUTION', 1, 'MC clear after APU')
	pushSeqCmd(0.5, 'PLT_MASTER_CAUTION', 0)
	pushSeqCmd(0.3, 'PLT_MASTER_WARNING', 1, 'MW clear after APU')
	pushSeqCmd(0.3, 'PLT_MASTER_WARNING', 0)

	# Open APU bleed air
	pushSeqCmd(dt, 'BLEED_APU', 1, 'APU bleed air - OPEN')
	pushSeqCmd(dt, 'scriptSpeech', 'Waiting for bleed air pressure.')

	# Wait for bleed pressure to reach 40 PSI
	pushSeqCmd(dt, 'scriptCockpitState',
		control='C-130J/BLEED_AIR_PRESSURE', value=40, condition='>=', duration=2)
	pushSeqCmd(dt, 'scriptSpeech', 'Bleed air pressure stable.')

	# APU switch - click left one detent (value 0) to settle in RUN.
	pushSeqCmd(dt, 'APU_SWITCH', 0, 'APU switch - click left to RUN')

	# MC clear after bleed stable
	pushSeqCmd(dt, 'PLT_MASTER_CAUTION', 1, 'MC clear after bleed')
	pushSeqCmd(0.5, 'PLT_MASTER_CAUTION', 0)
	pushSeqCmd(0.3, 'PLT_MASTER_WARNING', 1, 'MW clear after bleed')
	pushSeqCmd(0.3, 'PLT_MASTER_WARNING', 0)

	# --- AIR COND panel - Set (as required) ---
	pushSeqCmd(dt, 'AC_FLT_PWR', 1, 'Flt Station A/C - ON')
	pushSeqCmd(dt, 'AC_CARGO_PWR', 1, 'Cargo A/C - ON')

	# --- Master Caution reset + ECB reset (full procedure from in-game checklist) ---
	# MUST complete before engines can be started.
	pushSeqCmd(dt, 'scriptSpeech', 'Resetting master caution.')
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
	pushSeqCmd(dt, 'scriptSpeech', 'E C Bs reset complete.')
	# MC clear after ECB reset
	pushSeqCmd(dt, 'PLT_MASTER_CAUTION', 1, 'MC clear after ECB reset')
	pushSeqCmd(0.5, 'PLT_MASTER_CAUTION', 0)
	pushSeqCmd(0.3, 'PLT_MASTER_WARNING', 1, 'MW clear after ECB reset')
	pushSeqCmd(0.3, 'PLT_MASTER_WARNING', 0)

	# --- Elevator trim power to NORM (after power application) ---
	pushSeqCmd(dt, 'TRIM_ELEV_TAB_PWR', 2, 'Elev trim power - NORM')

	# CNI-MU initialization - wait for alignment to start
	pushSeqCmd(dt, 'scriptSpeech', 'C N I M U initialising. Allow time for alignment.')
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
	pushSeqCmd(dt, 'scriptSpeech', 'Starting engines checklist.')

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
	pushSeqCmd(dt, 'EXT_NAV', 2, 'Nav lights - STEADY')
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

	pushSeqCmd(dt, 'scriptSpeech', 'Engines at start. Holding 30 seconds for spool up.')

	# Press master caution periodically during the 30s hold
	pushSeqCmd(15.0, 'PLT_MASTER_CAUTION', 1, 'MC clear at 15s of hold')
	pushSeqCmd(0.5, 'PLT_MASTER_CAUTION', 0)
	pushSeqCmd(0.3, 'PLT_MASTER_WARNING', 1, 'MW clear at 15s of hold')
	pushSeqCmd(0.3, 'PLT_MASTER_WARNING', 0)
	pushSeqCmd(14.5, 'PLT_MASTER_CAUTION', 1, 'MC clear at 30s of hold')
	pushSeqCmd(0.5, 'PLT_MASTER_CAUTION', 0)
	pushSeqCmd(0.3, 'PLT_MASTER_WARNING', 1, 'MW clear at 30s of hold')
	pushSeqCmd(0.3, 'PLT_MASTER_WARNING', 0)

	# After 30s at START, click each engine one detent left back to RUN
	pushSeqCmd(dt, 'scriptSpeech', 'Releasing engine switches to run.')
	pushSeqCmd(dt, 'ENG_1_START_SWITCH', 0, 'Engine 1 - click left to RUN')
	pushSeqCmd(dt, 'ENG_2_START_SWITCH', 0, 'Engine 2 - click left to RUN')
	pushSeqCmd(dt, 'ENG_3_START_SWITCH', 0, 'Engine 3 - click left to RUN')
	pushSeqCmd(dt, 'ENG_4_START_SWITCH', 0, 'Engine 4 - click left to RUN')

	# Master caution clear after engines settled
	pushSeqCmd(dt, 'PLT_MASTER_CAUTION', 1, 'MC clear after engines at RUN')
	pushSeqCmd(0.5, 'PLT_MASTER_CAUTION', 0)
	pushSeqCmd(0.3, 'PLT_MASTER_WARNING', 1, 'MW clear after engines at RUN')
	pushSeqCmd(0.3, 'PLT_MASTER_WARNING', 0)

	# --- Post-engine-start: CNBP LSK L1 ---
	pushSeqCmd(dt, 'scriptSpeech', 'Engines running.')

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
	pushSeqCmd(dt, 'scriptSpeech', 'Generators online. A P U remains running.')
	pushSeqCmd(dt, 'ELECTRICAL_GENERATOR_1', 1, 'Gen 1 - ON')
	pushSeqCmd(dt, 'ELECTRICAL_GENERATOR_2', 1)
	pushSeqCmd(dt, 'ELECTRICAL_GENERATOR_3', 1)
	pushSeqCmd(dt, 'ELECTRICAL_GENERATOR_4', 1)

	# Periodic MC + MW press (press + release for both)
	pushSeqCmd(dt, 'PLT_MASTER_CAUTION', 1, 'MC periodic press')
	pushSeqCmd(0.3, 'PLT_MASTER_CAUTION', 0)
	pushSeqCmd(0.3, 'PLT_MASTER_WARNING', 1, 'MW periodic press')
	pushSeqCmd(0.3, 'PLT_MASTER_WARNING', 0)

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

	# Periodic MC + MW press
	pushSeqCmd(dt, 'PLT_MASTER_CAUTION', 1, 'MC periodic press')
	pushSeqCmd(0.3, 'PLT_MASTER_CAUTION', 0)
	pushSeqCmd(0.3, 'PLT_MASTER_WARNING', 1, 'MW periodic press')
	pushSeqCmd(0.3, 'PLT_MASTER_WARNING', 0)


	# ===========================================================================
	# CHECKLIST: TAXI
	# ===========================================================================

	# Taxi & wingtip taxi lights ON
	pushSeqCmd(dt, 'TAXI_LIGHT', 1, 'Taxi lights - ON')
	pushSeqCmd(dt, 'WINGTIP_TAXI', 1, 'Wingtip taxi - ON')

	# FLAPS 50%
	pushSeqCmd(dt, 'CC_FLAP_LEVER', int16(0.50), 'Flaps - 50%')


	# Periodic MC + MW press
	pushSeqCmd(dt, 'PLT_MASTER_CAUTION', 1, 'MC periodic press')
	pushSeqCmd(0.3, 'PLT_MASTER_CAUTION', 0)
	pushSeqCmd(0.3, 'PLT_MASTER_WARNING', 1, 'MW periodic press')
	pushSeqCmd(0.3, 'PLT_MASTER_WARNING', 0)

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
	# All CNI LSK buttons need an explicit press (value 1) AND release (value 0);
	# missing the release leaves the soft key visually "stuck down".
	#
	# Page flow (pilot CNI):
	#   <starting page> -> MC INDX  -> MSN CMPTR INDEX
	#   MSN CMPTR INDEX -> R1       -> DEF SYS CTRL
	#       DEF SYS CTRL -> L1 (MSTR PWR), L4 (MWS PWR), L5 (IRCM PWR)
	#       DEF SYS CTRL -> L3       -> CMDS sub-page
	#           CMDS    -> L3 (OTHER1 ARM), L4 (OTHER2 ARM), L5 (JMR INTF ON)
	#           CMDS    -> L6       -> back to DEF SYS CTRL
	#       DEF SYS CTRL -> L2       -> RWR sub-page
	#           RWR     -> R2 (SHOW UNK)
	#           RWR     -> L6       -> back to DEF SYS CTRL
	#   DEF SYS CTRL    -> MC INDX (x2) -> back out

	# Dismiss anything currently on R4/R5 (e.g. a residual scratchpad prompt)
	pushSeqCmd(dt,  'PLT_CNI_LSK_R4', 1, 'PLT CNI LSK R4 - press')
	pushSeqCmd(0.3, 'PLT_CNI_LSK_R4', 0, 'PLT CNI LSK R4 - release')
	pushSeqCmd(dt,  'PLT_CNI_LSK_R5', 1, 'PLT CNI LSK R5 - press')
	pushSeqCmd(0.3, 'PLT_CNI_LSK_R5', 0, 'PLT CNI LSK R5 - release')

	# Navigate: MC INDX -> MSN CMPTR INDEX -> DEF SYS> (R1)
	pushSeqCmd(dt, 'PLT_CNI_MC_INDX', 1, 'PLT CNI - to MSN CMPTR INDEX')
	pushSeqCmd(dt, 'PLT_CNI_LSK_R1',  1, 'MSN CMPTR INDEX R1 - DEF SYS>')

	# DEF SYS CTRL: power on MSTR/MWS/IRCM.
	# MWS (missile warning) and IRCM (IR countermeasures) drive the threat
	# audio tones; without them the CMDS audio warnings are silent on cold
	# start (they default on with a hot start).
	pushSeqCmd(dt,  'PLT_CNI_LSK_L1', 1, 'DEF SYS L1 - MSTR PWR ON')
	pushSeqCmd(0.3, 'PLT_CNI_LSK_L1', 0)
	pushSeqCmd(0.5, 'PLT_CNI_LSK_L4', 1, 'DEF SYS L4 - MWS PWR ON')
	pushSeqCmd(0.3, 'PLT_CNI_LSK_L4', 0)
	pushSeqCmd(0.5, 'PLT_CNI_LSK_L5', 1, 'DEF SYS L5 - IRCM PWR ON')
	pushSeqCmd(0.3, 'PLT_CNI_LSK_L5', 0)

	# CMDS sub-page (L3 from DEF SYS CTRL): arm OTHER1/OTHER2 and toggle JMR INTF ON.
	# Defaults are OTHER1/2 SAFE + JMR INTF OFF, so a single press flips each.
	pushSeqCmd(0.5, 'PLT_CNI_LSK_L3', 1, 'DEF SYS L3 - to CMDS page')
	pushSeqCmd(0.5, 'PLT_CNI_LSK_L3', 1, 'CMDS L3 - OTHER1 ARM')
	pushSeqCmd(0.5, 'PLT_CNI_LSK_L4', 1, 'CMDS L4 - OTHER2 ARM')
	pushSeqCmd(0.5, 'PLT_CNI_LSK_L5', 1, 'CMDS L5 - JMR INTF ON')
	pushSeqCmd(0.5, 'PLT_CNI_LSK_L6', 1, 'CMDS L6 - back to DEF SYS CTRL')

	# RWR sub-page (L2 from DEF SYS CTRL): toggle SHOW UNK on.
	pushSeqCmd(0.5, 'PLT_CNI_LSK_L2', 1, 'DEF SYS L2 - to RWR page')
	pushSeqCmd(0.5, 'PLT_CNI_LSK_R2', 1, 'RWR R2 - SHOW UNK toggle')
	pushSeqCmd(0.5, 'PLT_CNI_LSK_L6', 1, 'RWR L6 - back to DEF SYS CTRL')

	# Step back out twice (DEF SYS CTRL -> MSN CMPTR INDEX -> top)
	pushSeqCmd(dt, 'PLT_CNI_MC_INDX', 1, 'PLT CNI MC INDX - back (1/2)')
	pushSeqCmd(dt, 'PLT_CNI_MC_INDX', 1, 'PLT CNI MC INDX - back (2/2)')

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

	# Periodic MC + MW press
	pushSeqCmd(dt, 'PLT_MASTER_CAUTION', 1, 'MC periodic press')
	pushSeqCmd(0.3, 'PLT_MASTER_CAUTION', 0)
	pushSeqCmd(0.3, 'PLT_MASTER_WARNING', 1, 'MW periodic press')
	pushSeqCmd(0.3, 'PLT_MASTER_WARNING', 0)

	# --- Computer drop switch to AD-MAN/TJ-AUTO (middle position) ---
	pushSeqCmd(dt, 'ADP_COMP_DROP', 1, 'Computer Drop - AD-MAN/TJ-AUTO')

	# --- Pilot HUD: latch, TAC mode, NAV mode ---
	pushSeqCmd(dt, 'scriptSpeech', 'Configuring HUD.')
	pushSeqCmd(dt, 'PLT_HUD_LATCH',    1, 'Pilot HUD Latch - press')
	pushSeqCmd(dt, 'PLT_HUD_TAC_MODE', 1, 'Pilot HUD TAC mode - press')
	pushSeqCmd(dt, 'PLT_HUD_NAV_MODE', 1, 'Pilot HUD NAV mode - press')

	# --- NAV lights: bright + steady ---
	pushSeqCmd(dt, 'EXT_DIM', 1, 'Nav lights brightness - BRIGHT')
	pushSeqCmd(dt, 'EXT_NAV', 2, 'Nav lights mode - STEADY')

	# --- ARC-210: TR+G + SQL on ---
	pushSeqCmd(dt, 'scriptSpeech', 'Configuring A R C 2 1 0.')
	pushSeqCmd(dt, 'ARC210_OP_MODE', 1, 'ARC-210 op mode - TR+G')
	pushSeqCmd(dt, 'ARC210_SQL',     1, 'ARC-210 SQL - ON')

	# --- Standby ADI: cage then uncage to align ---
	pushSeqCmd(dt, 'scriptSpeech', 'Aligning standby attitude indicator.')
	pushSeqCmd(dt, 'STBY_ADI_CAGE', 1, 'Standby ADI - cage')
	pushSeqCmd(1.0, 'STBY_ADI_CAGE', 0, 'Standby ADI - uncage (release)')

	# Re-assert ATCS in case it got toggled off (clears ATCS OFF warning)
	pushSeqCmd(dt, 'ATCS_GUARD', 1, 'ATCS guard - up')
	pushSeqCmd(dt, 'ATCS', 1, 'ATCS - ON (re-assert)')
	pushSeqCmd(dt, 'ATCS_GUARD', 0, 'ATCS guard - down')

	# Night mode:
	#   - All internal cockpit lights OFF (panel/console/dome/flood/floor backlights)
	#   - All display screen brightness to lowest visible
	#   - All external lights ON (NAV steady bright, landing, taxi, leading edge)
	if vars.get('Time') == 'Night':
		pushSeqCmd(dt, 'scriptSpeech', 'Configuring night lighting.')

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
		pushSeqCmd(dt, 'EXT_NAV',        2, 'NAV lights - STEADY')
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

	# --- LSGI (Low Speed Ground Idle) select switches - press + release ---
	# Each switch is a momentary button: press (value 1) then release (value 0).
	# Engines 1 and 2 get a longer pre-press delay (~1.5s) - their FADECs occasionally
	# refuse the LSGI input if pressed back-to-back; the spacing makes it reliable.
	pushSeqCmd(dt, 'scriptSpeech', 'Setting low ground idle.')
	pushSeqCmd(1.5,  'CC_LSGI_ENGINE_1_SWITCH', 1, 'Engine 1 LSGI - press')
	pushSeqCmd(0.5,  'CC_LSGI_ENGINE_1_SWITCH', 0, 'Engine 1 LSGI - release')
	pushSeqCmd(1.5,  'CC_LSGI_ENGINE_2_SWITCH', 1, 'Engine 2 LSGI - press')
	pushSeqCmd(0.5,  'CC_LSGI_ENGINE_2_SWITCH', 0, 'Engine 2 LSGI - release')
	pushSeqCmd(0.5,  'CC_LSGI_ENGINE_3_SWITCH', 1, 'Engine 3 LSGI - press')
	pushSeqCmd(0.3,  'CC_LSGI_ENGINE_3_SWITCH', 0, 'Engine 3 LSGI - release')
	pushSeqCmd(0.5,  'CC_LSGI_ENGINE_4_SWITCH', 1, 'Engine 4 LSGI - press')
	pushSeqCmd(0.3,  'CC_LSGI_ENGINE_4_SWITCH', 0, 'Engine 4 LSGI - release')

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
	pushSeqCmd(dt, 'FADEC_GUARD_1', 0, 'Engine 1 FADEC guard - DOWN')
	pushSeqCmd(dt, 'FADEC_GUARD_2', 0, 'Engine 2 FADEC guard - DOWN')
	pushSeqCmd(dt, 'FADEC_GUARD_3', 0, 'Engine 3 FADEC guard - DOWN')
	pushSeqCmd(dt, 'FADEC_GUARD_4', 0, 'Engine 4 FADEC guard - DOWN')
	# Prop sync DOWN/ON (very last functional action)
	pushSeqCmd(dt, 'PROP_SYNC', 1, 'Prop sync - DOWN/ON')

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
	pushSeqCmd(dt,  'scriptSpeech', 'Countermeasures armed.')
	pushSeqCmd(0.5, 'scriptSpeech', 'Radar and altimeter powered on.')
	pushSeqCmd(0.5, 'scriptSpeech', 'Pilot action needed: set or deselect emergency parking brake.')
	pushSeqCmd(0.5, 'scriptSpeech', 'Set HUDs as desired.')

	# --- FINAL: Navigate both CNI-MUs to POWER UP, then engage AUTONAV + MSTR AV ON ---
	# POWER UP page is reached via INDX (INDEX 1/2) -> L1 (<POWER UP).
	# Page layout (per CNI_MU/pages/power_up.lua):
	#   L5 = ALIGN GPS/LAST/REF toggle
	#   R4 = MSTR AV ON   (toggle)
	#   R5 = AUTONAV      (toggle)
	# Pilot AND copilot must both be on POWER UP with position synced (GPS) before
	# AUTONAV / MSTR AV ON. These are the VERY LAST actions of the cold start.
	pushSeqCmd(0.5, 'scriptSpeech', 'G P S is aligning. Estimated wait time approximately five minutes from system power on.')

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

	pushSeqCmd(0.5, 'scriptSpeech', 'Synchronising pilot and copilot navigation. Verifying G P S position on both C N I units.')

	# --- Final actions: AUTONAV select, then MSTR AV ON select, on both CNIs ---
	pushSeqCmd(0.5, 'scriptSpeech', 'Engaging autonav.')
	pushSeqCmd(0.5, 'PLT_CNI_LSK_R5',  1, 'PLT CNI R5 - AUTONAV select')
	pushSeqCmd(0.3, 'PLT_CNI_LSK_R5',  0)
	pushSeqCmd(0.3, 'CPLT_CNI_LSK_R5', 1, 'CPLT CNI R5 - AUTONAV select')
	pushSeqCmd(0.3, 'CPLT_CNI_LSK_R5', 0)

	pushSeqCmd(0.5, 'scriptSpeech', 'Engaging master avionics.')
	pushSeqCmd(0.5, 'PLT_CNI_LSK_R4',  1, 'PLT CNI R4 - MSTR AV ON select')
	pushSeqCmd(0.3, 'PLT_CNI_LSK_R4',  0)
	pushSeqCmd(0.3, 'CPLT_CNI_LSK_R4', 1, 'CPLT CNI R4 - MSTR AV ON select')
	pushSeqCmd(0.3, 'CPLT_CNI_LSK_R4', 0)

	pushSeqCmd(0.5, 'scriptSpeech', 'Cold start complete.')

	return seq


###############################################################################
# SHUTDOWN
###############################################################################
def Shutdown(config, vars):
	seq = []
	seqTime = 0
	dt = 0.3

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
	pushSeqCmd(dt, 'scriptSpeech', 'Beginning shutdown. Parking brake set, throttles ground idle.')
	pushSeqCmd(dt, 'PARKING_BRAKE', 1, 'Parking brake - SET')

	# Exterior lights off
	pushSeqCmd(dt, 'LDG_LIGHT_L', 0)
	pushSeqCmd(dt, 'LDG_LIGHT_R', 0)
	pushSeqCmd(dt, 'LDG_MOTOR_L', 0, 'L landing - RETRACT')
	pushSeqCmd(dt, 'LDG_MOTOR_R', 0, 'R landing - RETRACT')
	pushSeqCmd(dt, 'TAXI_LIGHT', 0)
	pushSeqCmd(dt, 'WINGTIP_TAXI', 0)
	pushSeqCmd(dt, 'EXT_STROBE_TOP', 1, 'Top strobe - OFF')
	pushSeqCmd(dt, 'EXT_STROBE_BTM', 1, 'Bottom strobe - OFF')
	pushSeqCmd(dt, 'EXT_LEDGE', 0)

	# Defensive systems STBY
	pushSeqCmd(dt, 'DSP_ECM_MASTER', 0)
	pushSeqCmd(dt, 'DSP_IRCM_MASTER', 0)
	pushSeqCmd(dt, 'DSP_CMDS_MODE', 0)
	pushSeqCmd(dt, 'DSP_DEFENSIVE_MASTER_SWITCH', 0)

	# Radar OFF
	pushSeqCmd(dt, 'RCP_MASTER_POWER', 0)

	# Pitot/NESA heat OFF
	pushSeqCmd(dt, 'ICE_PITOT_P', 0)
	pushSeqCmd(dt, 'ICE_PITOT_CP', 0)
	pushSeqCmd(dt, 'ICE_NESA_CTR', 0)
	pushSeqCmd(dt, 'ICE_NESA_SIDE', 0)

	# Start APU for electrical transition (spring-loaded - release from START fires start)
	pushSeqCmd(dt, 'scriptSpeech', 'Starting A P U for electrical transition.')
	pushSeqCmd(dt, 'APU_SWITCH', 2, 'APU - START')
	pushSeqCmd(2.0, 'APU_SWITCH', 1, 'APU - RUN (release from spring)')
	pushSeqCmd(dt, 'scriptCockpitState',
		control='C-130J/APU_NG', value=100, condition='>=', duration=2)
	pushSeqCmd(dt, 'ELECTRICAL_EXT_POWER_APU', 2, 'EXT PWR/APU - APU')
	pushSeqCmd(dt, 'BLEED_APU', 1, 'APU bleed - OPEN')

	# Engine shutdown
	pushSeqCmd(dt, 'scriptSpeech', 'Shutting down engines.')
	pushSeqCmd(dt, 'ELECTRICAL_GENERATOR_1', 0)
	pushSeqCmd(dt, 'ELECTRICAL_GENERATOR_2', 0)
	pushSeqCmd(dt, 'ELECTRICAL_GENERATOR_3', 0)
	pushSeqCmd(dt, 'ELECTRICAL_GENERATOR_4', 0)
	pushSeqCmd(dt, 'PROP_SYNC', 0)
	pushSeqCmd(dt, 'ATCS_GUARD', 1)
	pushSeqCmd(dt, 'ATCS', 0)
	pushSeqCmd(dt, 'ATCS_GUARD', 0)

	# Engine start switches are relative-click controls (see ColdStart for full
	# explanation). Clicking right from RUN steps the detent toward STOP via
	# the simulator's switch-wrap behaviour.
	pushSeqCmd(dt, 'ENG_1_START_SWITCH', 1, 'Engine 1 - click toward STOP')
	pushSeqCmd(dt, 'ENG_2_START_SWITCH', 1, 'Engine 2 - click toward STOP')
	pushSeqCmd(dt, 'ENG_3_START_SWITCH', 1, 'Engine 3 - click toward STOP')
	pushSeqCmd(dt, 'ENG_4_START_SWITCH', 1, 'Engine 4 - click toward STOP')
	pushSeqCmd(20.0, '', '', 'Engines spooling down')
	pushSeqCmd(dt, 'scriptSpeech', 'Engines stopped.')

	# Hydraulics OFF
	pushSeqCmd(dt, 'HYD_ENG_PUMP_1_UTIL', 0)
	pushSeqCmd(dt, 'HYD_ENG_PUMP_2_UTIL', 0)
	pushSeqCmd(dt, 'HYD_ENG_PUMP_3_BOOST', 0)
	pushSeqCmd(dt, 'HYD_ENG_PUMP_4_BOOST', 0)
	pushSeqCmd(dt, 'HYD_AUX_PUMP', 0)
	pushSeqCmd(dt, 'HYD_SUCT_BOOST_UTIL', 0)
	pushSeqCmd(dt, 'HYD_SUCT_BOOST_BOOST', 0)

	# Flight control boost OFF
	for cvr, sw in [
		('CTRL_BOOST_AILERON_BOOST_GUARD','CTRL_BOOST_AILERON_BOOST'),
		('CTRL_BOOST_AILERON_UTIL_GUARD','CTRL_BOOST_AILERON_UTIL'),
		('CTRL_BOOST_RUDDER_BOOST_GUARD','CTRL_BOOST_RUDDER_BOOST'),
		('CTRL_BOOST_RUDDER_UTIL_GUARD','CTRL_BOOST_RUDDER_UTIL'),
		('CTRL_BOOST_ELEVATOR_BOOST_GUARD','CTRL_BOOST_ELEVATOR_BOOST'),
		('CTRL_BOOST_ELEVATOR_UTIL_GUARD','CTRL_BOOST_ELEVATOR_UTIL'),
	]:
		pushSeqCmd(dt, cvr, 1)
		pushSeqCmd(dt, sw, 0)
		pushSeqCmd(dt, cvr, 0)

	pushSeqCmd(dt, 'TRIM_ELEV_TAB_PWR', 0)
	pushSeqCmd(dt, 'CC_FLAP_LEVER', 0, 'Flaps - UP')

	# A/C OFF
	pushSeqCmd(dt, 'AC_FLT_PWR', 0)
	pushSeqCmd(dt, 'AC_CARGO_PWR', 0)

	# Anti-skid OFF
	pushSeqCmd(dt, 'ANTI_SKID', 0)

	# APU shutdown
	pushSeqCmd(dt, 'BLEED_APU', 0, 'APU bleed - CLOSED')
	pushSeqCmd(dt, 'ELECTRICAL_EXT_POWER_APU', 1, 'EXT PWR/APU - OFF')
	pushSeqCmd(dt, 'APU_SWITCH', 0, 'APU - STOP')

	# Lighting off
	pushSeqCmd(dt, 'PLT_CC_LIGHTING_MASTER_DISPLAY_BRIGHTNESS', 0)
	pushSeqCmd(dt, 'CPLT_CC_LIGHTING_MASTER_DISPLAY_BRIGHTNESS', 0)
	pushSeqCmd(dt, 'PLT_CC_LIGHTING_PANEL_BACKLIGHTING', 0)
	pushSeqCmd(dt, 'CPLT_CC_LIGHTING_PANEL_BACKLIGHTING', 0)
	pushSeqCmd(dt, 'PLT_CC_LIGHTING_FLOOD_LIGHT_BRIGHTNESS', 0)
	pushSeqCmd(dt, 'CPLT_CC_LIGHTING_FLOOD_LIGHT_BRIGHTNESS', 0)
	pushSeqCmd(dt, 'CPLT_CC_LIGHTING_OVERHEAD_PANEL_BACKLIGHTING', 0)
	pushSeqCmd(dt, 'CPLT_CC_LIGHTING_OVERHEAD_FLOOD_LIGHT_BRIGHTNESS', 0)
	pushSeqCmd(dt, 'CPLT_CC_LIGHTING_CONSOLE_LIGHT_BRIGHTNESS', 0)
	pushSeqCmd(dt, 'PLT_CC_LIGHTING_FLOOR_LIGHT_BRIGHTNESS', 0)
	pushSeqCmd(dt, 'PLT_CC_LIGHTING_DOME_BRIGHTNESS', 0)
	pushSeqCmd(dt, 'EXT_NAV', 1, 'Nav - OFF')

	# Battery OFF
	pushSeqCmd(dt, 'ELECTRICAL_BATTERY', 0, 'Battery - OFF')

	pushSeqCmd(dt, 'scriptSpeech', 'Shutdown complete. Aircraft is cold and dark.')
	return seq


###############################################################################
# TEST: Engine Switch Position - send one click direction to all 4 engines.
#   value 0 = click switch one detent to the LEFT
#   value 1 = click switch one detent to the RIGHT
# Use this to nudge engines one detent at a time and observe the result.
###############################################################################
def TestEngineSwitches(config, vars):
	seq = []
	seqTime = 0
	dt = 0.3
	value = int(vars.get('Direction', '1'))
	direction = 'right' if value == 1 else 'left'

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

	pushSeqCmd(0, '', '', f'Engine switch test - all engines click {direction}')
	pushSeqCmd(dt, 'scriptSpeech', f'Clicking all four engine switches {direction}.')

	pushSeqCmd(dt, 'ENG_1_START_SWITCH', value, f'Engine 1 - click {direction}')
	pushSeqCmd(dt, 'ENG_2_START_SWITCH', value, f'Engine 2 - click {direction}')
	pushSeqCmd(dt, 'ENG_3_START_SWITCH', value, f'Engine 3 - click {direction}')
	pushSeqCmd(dt, 'ENG_4_START_SWITCH', value, f'Engine 4 - click {direction}')

	pushSeqCmd(dt, 'scriptSpeech', f'Click {direction} sent. Note position.')
	return seq

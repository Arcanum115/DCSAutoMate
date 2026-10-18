# Return a Dictionary of script data.  The 'scripts' key is a list of scripts that users will be selecting from.  Each script has an associated 'function', which is the name of the function in this file that will be called to generate the command sequence, and a dictionary of 'vars' that the user will be prompted to choose from before running the script, and will be passed into the sequence generating function.
def getScriptData():
	return {
		'moduleName': 'C-130J-30',
		'scripts': [
			{
				'name': 'Cold Start',
				'function': 'ColdStart',
				'vars': {
					'time': {
						'label': 'Time',
						'options': {
							'day': 'Day',
							'night': 'Night',
						},
					},
					'electronicCircuitBreakers': {
						'label': 'Electronic Circuit Breakers',
						'options': {
							'reset': 'Reset',
							'dontReset': 'Don\'t Reset',
						},
					},
					'apu': {
						'label': 'APU',
						'options': {
							'leaveOn': 'Leave on at the end',
							'turnOff': 'Turn off at the end',
						},
					},
				},
			},
			{
				'name': 'Hot Start',
				'function': 'HotStart',
				'vars': {
					'time': {
						'label': 'Time',
						'options': {
							'day': 'Day',
							'night': 'Night',
						},
					},
					'apu': {
						'label': 'APU',
						'options': {
							'leaveOn': 'Leave on at the end',
							'turnOff': 'Turn off at the end',
						},
					},
				},
			},
			{
				'name': 'Air Start',
				'function': 'AirStart',
				'vars': {
					'time': {
						'label': 'Time',
						'options': {
							'day': 'Day',
							'night': 'Night',
						},
					},
				},
			},
			{
				'name': 'Shutdown',
				'function': 'Shutdown',
				'vars': {},
			},
			#{
			#	'name': 'Test',
			#	'function': 'Test',
			#	'vars': {
			#		'time': {
			#			'label': 'Time',
			#			'options': {
			#				'day': 'Day',
			#				'night': 'Night',
			#			},
			#		},
			#		'apu': {
			#			'label': 'APU',
			#			'options': {
			#				'leaveOn': 'Leave on at the end',
			#				'turnOff': 'Turn off at the end',
			#			},
			#		},
			#	},
			#},
		],
	}


def getInfo():
	return ''

def Test(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	# Test code here...
	pushSeqCmd(0, '', '', "Running Test sequence")


	return seq

###############################################################################
###############################################################################
def ColdStart(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	pushSeqCmd(0, '', '', 'Running Cold Start sequence')

	# Oil Cooler Flap switches ... AUTO (rear overhead panel)
	pushSeqCmd(dt, 'MECH_INTERFACE.oil_flap_1_auto', 1)  # Engine 1 oil cooler flap ... AUTO
	pushSeqCmd(dt, 'MECH_INTERFACE.oil_flap_2_auto', 1)  # Engine 2 oil cooler flap ... AUTO
	pushSeqCmd(dt, 'MECH_INTERFACE.oil_flap_3_auto', 1)  # Engine 3 oil cooler flap ... AUTO
	pushSeqCmd(dt, 'MECH_INTERFACE.oil_flap_4_auto', 1)  # Engine 4 oil cooler flap ... AUTO

	# Generator switches 1-4 ... ON (forward overhead panel)
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.gen_1', 1)  # GEN 1 switch ... ON
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.gen_2', 1)  # GEN 2 switch ... ON
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.gen_3', 1)  # GEN 3 switch ... ON
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.gen_4', 1)  # GEN 4 switch ... ON

	# Battery switch ... ON
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.battery', 1)  # BTRY switch ... ON
	# APU start switch ... RUN right after battery power (fork change).  Positive value steps: STOP -> RUN -> START.
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.apu_selector', 1) # STOP -> RUN

	# Wait 50 seconds for avionics to power up (APU will not start until then).
	pushSeqCmd(dt, 'scriptText', 'Waiting for avionics to power up (50 sec)...')
	pushSeqCmd(50, 'scriptText', 'Avionics should be powered up now.')

	# Master Caution ... Reset
	pushSeqCmd(dt, 'PILOT_REF_MODE_PANEL.master_caution', 1)  # press
	pushSeqCmd(dt, 'PILOT_REF_MODE_PANEL.master_caution', 0)  # release

	# APU start: hold START for 5 sec, then release to RUN
	# ENGINE_APU_CTRL.apu_selector: positive value steps: STOP -> RUN -> START; negative value steps: START -> RUN -> STOP
	# ENGINE_APU_CTRL.apu_select_stop: 1 = STOP, 0 = RUN
	# The switch is already at RUN (set right after battery on), so one step reaches START.
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.apu_selector', 1) # APU start switch ... RUN -> START
	pushSeqCmd(5, 'ENGINE_APU_CTRL.apu_selector', -1) # Release to RUN, positive value steps: STOP -> RUN -> START; negative value steps: START -> RUN -> STOP
	pushSeqCmd(dt, 'scriptText', 'APU starting. Waiting 30 sec for 100% RPM...')
	pushSeqCmd(30, 'scriptText', 'APU should be at 100% RPM.')

	# External Power/APU switch ... APU
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.ext_elec', 2)  # 0 = EXT PWR, 1 = OFF, 2 = APU

	# NOTE: GPS acquisition starts when aircraft is on APU power.  Takes 1 minute, but we don't need a timer, because it'll have acquired by the time the engines are started.

	# Wait 8 seconds for the remaining avionics to power up.
	pushSeqCmd(dt, 'scriptText', 'Waiting for remaining avionics to power up (8 sec)...')
	pushSeqCmd(8, 'scriptText', 'Remaining avionics should be powered up now.')

	# Reset Electronic Circuit Breakers (if selected)
	if vars['electronicCircuitBreakers'] == 'reset':
		pushSeqCmd(dt, 'scriptSpeech', 'Resetting Electronic Circuit Breakers.')
		# Press CNBP ECB Key to open ECB page
		pushSeqCmd(dt, 'CNBP.cmd_3023', 1)  # ECB key ... press
		pushSeqCmd(dt, 'CNBP.cmd_3023', 0)  # release
		# Type 2 then press LSK L1 (HDD) to display ECBs on HDD 2
		pushSeqCmd(dt, 'CNBP.cmd_3003', 1)  # 2 key ... press
		pushSeqCmd(dt, 'CNBP.cmd_3003', 0)  # release
		pushSeqCmd(dt, 'CNBP.cmd_3013', 1)  # LSK L1 (HDD) ... press
		pushSeqCmd(dt, 'CNBP.cmd_3013', 0)  # release
		# Enter ECB circuit numbers: 481 482 483 902 108 109 609 613.  Typed at our legacy speed (fork change): 0.1 s press, 0.1 s release.
		# CNBP number keys: 0 = cmd_3001, 1 = cmd_3002 ... 9 = cmd_3010.
		for digit in '481482483902108109609613':
			pushSeqCmd(0.1, f'CNBP.cmd_{3001 + int(digit)}', 1, f'ECB digit {digit}')
			pushSeqCmd(0.1, f'CNBP.cmd_{3001 + int(digit)}', 0)
		# Press LSK R1 (RESET) twice to reset and confirm
		pushSeqCmd(dt, 'CNBP.cmd_3017', 1)  # LSK R1 (RESET) ... press
		pushSeqCmd(dt, 'CNBP.cmd_3017', 0)  # release
		pushSeqCmd(dt, 'CNBP.cmd_3017', 1)  # Confirm ... press
		pushSeqCmd(dt, 'CNBP.cmd_3017', 0)  # release
		# Press LSK L1 again to turn off ECB page and restore HDD
		pushSeqCmd(dt, 'CNBP.cmd_3013', 1)  # LSK L1 (HDD/OFF) ... press
		pushSeqCmd(dt, 'CNBP.cmd_3013', 0)  # release

	# APU Bleed Air ... OPEN
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.bleed_apu', 1) # Press
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.bleed_apu', 0) # Release

	# ELEV TRIM TAB switch ... NORM
	pushSeqCmd(dt, 'MECH_INTERFACE.elev_trim', 2)  # 0 = EMER, 1 = OFF, 2 = NORM

	# Master Avionics - ON
	pushSeqCmd(dt, 'P_CNI.SELECT_10', 1) # MSTR AV ON
	pushSeqCmd(dt, 'P_CNI.SELECT_10', 0) # Release

	# Pilot Oxygen Diluter Lever ... NORMAL OXYGEN
	pushSeqCmd(dt, 'PLANE_ATM.cmd_3029', 0) # NORMAL OXYGEN
	# Copilot Oxygen Diluter Lever ... NORMAL OXYGEN
	pushSeqCmd(dt, 'PLANE_ATM.cmd_3034', 0) # NORMAL OXYGEN # NOTE The label for this is swapped with the 'Copilot Oxygen Supply Lever'.  This appears to be a bug.

	# Turn on and set up HUD for pilot and copilot.
	# Pilot HUD
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3023', 1) # Pilot HUD latch ... deploy (down)
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3025', 1) # Pilot HUD BRT knob ... pull ON
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3027', 1) # Pilot HUD NAV mode ... ON
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3027', 0) # release
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3028', 1) # Pilot HUD TACT mode ... ON
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3028', 0) # release
	# Pilot HUD UNCG is left off (fork change): no velocity vector uncage.
	# Copilot HUD
	pushSeqCmd(dt, 'C_DISPLAYS.cmd_3023', 1) # Copilot HUD latch ... deploy (down)
	pushSeqCmd(dt, 'C_DISPLAYS.cmd_3025', 1) # Copilot HUD BRT knob ... pull ON
	pushSeqCmd(dt, 'C_DISPLAYS.cmd_3027', 1) # Copilot HUD NAV mode ... ON
	pushSeqCmd(dt, 'C_DISPLAYS.cmd_3027', 0) # release
	pushSeqCmd(dt, 'C_DISPLAYS.cmd_3028', 1) # Copilot HUD TACT mode ... ON
	pushSeqCmd(dt, 'C_DISPLAYS.cmd_3028', 0) # release
	pushSeqCmd(dt, 'C_DISPLAYS.cmd_3029', 1) # Copilot HUD UNCG ... uncage velocity vector
	pushSeqCmd(dt, 'C_DISPLAYS.cmd_3029', 0) # release

	# Pressurization Mode knob ... AUTO
	pushSeqCmd(dt, 'PLANE_ATM.cmd_3012', 2) # 0 = CONST ALT, 1 = MAN, 2 = AUTO, 3 = NO PRESS, 4 = AUX VENT

	# Air Conditioning POWER buttons ... ON (forward overhead panel)
	pushSeqCmd(dt, 'PLANE_ATM.cmd_3001', 1) # Flight Station A/C Power ... ON
	pushSeqCmd(dt, 'PLANE_ATM.cmd_3001', 0) # Release
	pushSeqCmd(dt, 'PLANE_ATM.cmd_3002', 1) # Cargo Compartment A/C Power ... ON
	pushSeqCmd(dt, 'PLANE_ATM.cmd_3002', 0) # Release

	# Hydraulic system
	pushSeqCmd(dt, 'HYDRAULICS.aux_pump', 1) # AUX PUMP switch ... ON
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.anti_skid', 1) # ANTI-SKID switch ... ON
	pushSeqCmd(dt, 'HYDRAULICS.suction_boost_pump_boost', 1) # SUCTION BOOST PUMP switch ... ON
	pushSeqCmd(dt, 'HYDRAULICS.suction_boost_pump_boost', 0) # Release
	pushSeqCmd(dt, 'HYDRAULICS.suction_boost_pump_util', 1) # UTILITY SUCTION BOOST PUMP switch ... ON
	pushSeqCmd(dt, 'HYDRAULICS.suction_boost_pump_util', 0) # Release

	# Exterior lighting (forward overhead panel left) (fork change, from our legacy script).
	# Positions per the module's own keybind labels: strobes 0 = WHITE, 1 = OFF, 2 = RED (our old DCS BIOS script sent 0.0 here, which is OFF).
	pushSeqCmd(dt, 'LIGHTING_PANELS.ext_master', 0) # Exterior Lighting Master switch ... NORM, 0 = NORM, 1 = OVERRIDE
	pushSeqCmd(dt, 'LIGHTING_PANELS.ext_nav', 0) # Navigation Light Mode switch ... STEADY, 0 = STEADY, 1 = OFF, 2 = FLASH
	if vars['time'] == 'night':
		pushSeqCmd(dt, 'LIGHTING_PANELS.ext_strobe_top', 2) # Top Strobe Light switch ... RED, 0 = WHITE, 1 = OFF, 2 = RED
		pushSeqCmd(dt, 'LIGHTING_PANELS.ext_strobe_btm', 2) # Bottom Strobe Light switch ... RED, 0 = WHITE, 1 = OFF, 2 = RED
		pushSeqCmd(dt, 'LIGHTING_PANELS.ext_dim', 1) # Navigation Light Brightness switch ... BRIGHT
		pushSeqCmd(dt, 'LIGHTING_PANELS.ext_ledge', 1) # Leading Edge Light switch ... ON
		pushSeqCmd(dt, 'LIGHTING_PANELS.landing_left_position', 2) # Left Landing Light Motor switch ... EXTEND, 0 = RETRACT, 1 = HOLD, 2 = EXTEND
		pushSeqCmd(dt, 'LIGHTING_PANELS.landing_right_position', 2) # Right Landing Light Motor switch ... EXTEND
		pushSeqCmd(dt, 'LIGHTING_PANELS.landing_left', 1) # Left Landing Light switch ... ON
		pushSeqCmd(dt, 'LIGHTING_PANELS.landing_right', 1) # Right Landing Light switch ... ON
		pushSeqCmd(dt, 'LIGHTING_PANELS.taxi_light_wheels', 1) # Taxi Lights switch ... ON
		pushSeqCmd(dt, 'LIGHTING_PANELS.taxi_light_wings', 1) # Wingtip Taxi Lights switch ... ON
	else:
		pushSeqCmd(dt, 'LIGHTING_PANELS.ext_strobe_top', 1) # Top Strobe Light switch ... OFF, 0 = WHITE, 1 = OFF, 2 = RED
		pushSeqCmd(dt, 'LIGHTING_PANELS.ext_strobe_btm', 1) # Bottom Strobe Light switch ... OFF, 0 = WHITE, 1 = OFF, 2 = RED
		pushSeqCmd(dt, 'LIGHTING_PANELS.ext_dim', 0) # Navigation Light Brightness switch ... DIM
		pushSeqCmd(dt, 'LIGHTING_PANELS.ext_ledge', 0) # Leading Edge Light switch ... OFF
		pushSeqCmd(dt, 'LIGHTING_PANELS.landing_left_position', 0) # Left Landing Light Motor switch ... RETRACT
		pushSeqCmd(dt, 'LIGHTING_PANELS.landing_right_position', 0) # Right Landing Light Motor switch ... RETRACT
		pushSeqCmd(dt, 'LIGHTING_PANELS.landing_left', 0) # Left Landing Light switch ... OFF
		pushSeqCmd(dt, 'LIGHTING_PANELS.landing_right', 0) # Right Landing Light switch ... OFF
		pushSeqCmd(dt, 'LIGHTING_PANELS.taxi_light_wheels', 0) # Taxi Lights switch ... OFF
		pushSeqCmd(dt, 'LIGHTING_PANELS.taxi_light_wings', 0) # Wingtip Taxi Lights switch ... OFF
		pushSeqCmd(dt, 'LIGHTING_PANELS.covert_form_brt', 1) # Covert/Formation Light Brightness ... MAX

	# Interior lighting
	if vars['time'] == 'night':
		pushSeqCmd(dt, 'LIGHTING_PANELS.pilot_side_panel', 0.5) # Pilot Panel Backlighting ... 50%
		pushSeqCmd(dt, 'LIGHTING_PANELS.pilot_side_flood', 0.3) # Pilot Panel Flood Lighting ... 30%
		pushSeqCmd(dt, 'LIGHTING_PANELS.copilot_side_panel', 0.5) # Copilot Panel Backlighting ... 50%
		pushSeqCmd(dt, 'LIGHTING_PANELS.copilot_side_flood', 0.3) # Copilot Panel Flood Lighting ... 30%
		pushSeqCmd(dt, 'LIGHTING_PANELS.cp_ctrl_cnsl', 0.5) # Center Console Backlighting ... 50%
		pushSeqCmd(dt, 'LIGHTING_PANELS.overhead', 0.5) # Overhead Panel Backlighting ... 50%

	# Backup ADI ... Uncage
	pushSeqCmd(dt, 'MECH_INTERFACE.pitch_bar', 0.25) # Move pitch bar down.
	pushSeqCmd(dt, 'MECH_INTERFACE.pitch_bar', 0.51) # Move pitch bar back up to uncage.  NOTE If you do it to 0.50 exactly, it will not uncage, it must be slightly more or less than 0.50.
	pushSeqCmd(dt, 'MECH_INTERFACE.pitch_bar', 0.5) # Move pitch bar to center.

	# Anti-Icing systems (ICE PROTECTION panel, rear overhead panel left)
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.ice_prop_1', 1) # Propeller 1 Ice Protection switch ... AUTO, 0 = ON, 1 = AUTO, 2 = OFF
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.ice_prop_2', 1) # Propeller 2 Ice Protection switch ... AUTO, 0 = ON, 1 = AUTO, 2 = OFF
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.ice_prop_3', 1) # Propeller 3 Ice Protection switch ... AUTO, 0 = ON, 1 = AUTO, 2 = OFF
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.ice_prop_4', 1) # Propeller 4 Ice Protection switch ... AUTO, 0 = ON, 1 = AUTO, 2 = OFF
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.ice_pitot_c', 0) # Pilot Pitot Heat switch ... ON, 0 = ON, 1 = OFF
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.ice_pitot_cp', 0) # Copilot Pitot Heat switch ... ON, 0 = ON, 1 = OFF
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.ice_nesa_ctr', 0) # Center NESA Heat switch ... ON, 0 = ON, 1 = OFF
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.ice_nesa_side', 0) # Side/Lower NESA Heat switch ... ON, 0 = ON, 1 = OFF

	# RADAR MASTER knob ... ON
	pushSeqCmd(dt, 'NAV_RADAR.master_mode', 1) # 0 = OFF, 1 = ON, 2 = TEST

	# Set throttles to GND IDLE and keep them there through engine startup (no physical throttle input needed).
	pushSeqCmd(dt, 'scriptSimCommand', 'iCommandPlaneThrustCommon', 'Throttles to GND IDLE', value=0.678, hold=True)

	# Start all four engines together (fork change, as in our legacy script; DCS doesn't enforce the 3-4-2-1 order).
	# ENGINE_APU_CTRL.engine_N_start_select: positive value steps: MOTOR -> STOP -> RUN -> START; negative value steps: START -> RUN -> STOP -> MOTOR
	pushSeqCmd(dt, 'scriptSpeech', 'Starting all engines.')
	for engine in (1, 2, 3, 4):
		pushSeqCmd(dt, f'ENGINE_APU_CTRL.engine_{engine}_start_select', 1) # STOP -> RUN
		pushSeqCmd(dt, f'ENGINE_APU_CTRL.engine_{engine}_start_select', 1) # RUN -> START
	# Hold START for 5 sec, then release each to RUN.
	pushSeqCmd(5, 'ENGINE_APU_CTRL.engine_1_start_select', -1) # Release to RUN
	for engine in (2, 3, 4):
		pushSeqCmd(dt, f'ENGINE_APU_CTRL.engine_{engine}_start_select', -1) # Release to RUN
	pushSeqCmd(dt, 'scriptText', 'Engines starting. Waiting 45 sec for ground idle...')
	# Let go of the throttle hold once the engines are at ground idle (fork change: no announcement).  The throttles stay at GND IDLE until the physical throttle moves.
	pushSeqCmd(45, 'scriptSimCommand', 'iCommandPlaneThrustCommon', release=True)

	# GPS acquisition takes 1 minute from when aircraft goes onto APU power.  By the time we get here (after engine start), it should have acquired.
	pushSeqCmd(dt, 'P_CNI.INDEX', 1) # INDX button
	pushSeqCmd(dt, 'P_CNI.INDEX', 0) # Release
	pushSeqCmd(dt, 'P_CNI.SELECT_1', 1) # POWER UP
	pushSeqCmd(dt, 'P_CNI.SELECT_1', 0) # Release
	pushSeqCmd(dt, 'P_CNI.SELECT_11', 1) # AUTONAV
	pushSeqCmd(dt, 'P_CNI.SELECT_11', 0) # Release

	# Defensive systems (fork change, from our legacy script).
	# Pilot CNI navigation re-anchors on MC INDX -> MSN CMPTR INDEX -> R1 (DEF SYS CTRL) before every sub-page, so a dropped press can't land on the wrong page.
	# That matters: on DEF SYS CTRL, L4/L5 are the MWS/IRCM power toggles, so a mis-landed press would power one OFF.
	def cni(key, msg, settle=1.0):
		pushSeqCmd(settle, f'P_CNI.{key}', 1, msg)
		pushSeqCmd(0.3, f'P_CNI.{key}', 0)

	def defSysCtrl(settle):
		cni('MC_INDX', 'MC INDX ... MSN CMPTR INDEX', settle)
		cni('SELECT_7', 'R1 ... DEF SYS CTRL')

	defSysCtrl(dt)
	# MSTR PWR powers MWS, IRCM and the rest.  Don't press L4 (MWS PWR) or L5 (IRCM PWR) afterwards: they'd toggle back OFF.
	cni('SELECT_1', 'DEF SYS CTRL L1 ... MSTR PWR ON')
	pushSeqCmd(2.0, '', '', 'Wait for MSTR PWR to power the defensive systems')
	# CMDS page: OTHER1 ARM, OTHER2 ARM, JMR INTF ON (defaults are SAFE, SAFE, OFF, so one press each).
	defSysCtrl(dt)
	cni('SELECT_3', 'DEF SYS CTRL L3 ... CMDS')
	cni('SELECT_3', 'CMDS L3 ... OTHER1 ARM')
	cni('SELECT_4', 'CMDS L4 ... OTHER2 ARM', 0.5)
	cni('SELECT_5', 'CMDS L5 ... JMR INTF ON', 0.5)
	# RWR page: SHOW UNK on, then the audio and missile launch tests.
	defSysCtrl(0.5)
	cni('SELECT_2', 'DEF SYS CTRL L2 ... RWR')
	cni('SELECT_8', 'RWR R2 ... SHOW UNK ON')
	cni('SELECT_9', 'RWR R3 ... FTI ENABLE', 0.8)
	cni('SELECT_10', 'RWR R4 ... AUDIO TEST', 0.8)
	cni('SELECT_11', 'RWR R5 ... MSL LAUNCH TEST', 0.8)
	cni('MC_INDX', 'MC INDX ... back out', 0.5)

	# DEFENSIVE SYSTEMS panel
	pushSeqCmd(dt, 'CMS_MGR.emerg_jett_cover', 0) # CMS Jettison switch guard ... closed
	pushSeqCmd(dt, 'CMS_MGR.emerg_jett', 0) # CMS Jettison switch ... OFF
	pushSeqCmd(dt, 'CMS_MGR.arm_toggle_cms', 1) # DEFENSIVE SYSTEMS MASTER switch ... OPR, 0 = STBY, 1 = OPR
	pushSeqCmd(dt, 'CMS_MGR.mws_arm', 1) # ECM switch ... OPR, 0 = STBY, 1 = OPR
	pushSeqCmd(dt, 'CMS_MGR.ircm_toggle', 1) # IRCM switch ... OPR, 0 = STBY, 1 = OPR
	pushSeqCmd(dt, 'CMS_MGR.cms_profile_mode', 3) # CMDS knob ... AUTO, 0 = OFF, 1 = MAN, 2 = SEMI, 3 = AUTO, 4 = BYP
	pushSeqCmd(dt, 'CMS_MGR.rwr_sep', 1) # RWR TGT SEP ... press
	pushSeqCmd(dt, 'CMS_MGR.rwr_sep', 0) # release
	pushSeqCmd(dt, 'CMS_MGR.rwr_search', 1) # RWR SRCH ... press
	pushSeqCmd(dt, 'CMS_MGR.rwr_search', 0) # release

	# Pilot RWR volume knob ... pull to monitor, then 50%
	pushSeqCmd(dt, 'VOLUME_MANAGER.rwr_pull', 1) # Pull to monitor
	pushSeqCmd(dt, 'VOLUME_MANAGER.rwr', 0.5) # 50%

	# Computer Drop switch ... AD-MAN/TJ-AUTO (middle)
	pushSeqCmd(dt, 'MECH_INTERFACE.computer_drop', 1) # 0, 1 = AD-MAN/TJ-AUTO (middle), 2

	# ARC-210 radio ... TR+G, squelch ON (fork change, from our legacy script)
	pushSeqCmd(dt, 'VOLUME_MANAGER.arc_op_mode', 1) # 0 = OFF, 1 = TR+G, 2 = TR, 3 = ADF, 4 = CHG PRST, 5 = TEST, 6 = ZERO (PULL)
	pushSeqCmd(dt, 'VOLUME_MANAGER.arc_sql', 1) # Squelch switch ... ON

	# CNI-MU and AMU displays (fork change, from our legacy script).
	# Pilot CNI back to POWER UP (its AUTONAV and MSTR AV ON were selected above; pressing them again would toggle them off).
	pushSeqCmd(dt, 'P_CNI.INDEX', 1) # INDX button
	pushSeqCmd(0.3, 'P_CNI.INDEX', 0) # Release
	pushSeqCmd(0.5, 'P_CNI.SELECT_1', 1) # L1 ... POWER UP
	pushSeqCmd(0.3, 'P_CNI.SELECT_1', 0) # Release
	# Copilot CNI ... POWER UP, then AUTONAV (R5) and MSTR AV ON (R4).
	pushSeqCmd(0.5, 'C_CNI.INDEX', 1) # INDX button
	pushSeqCmd(0.3, 'C_CNI.INDEX', 0) # Release
	pushSeqCmd(0.5, 'C_CNI.SELECT_1', 1) # L1 ... POWER UP
	pushSeqCmd(0.3, 'C_CNI.SELECT_1', 0) # Release
	pushSeqCmd(0.5, 'C_CNI.SELECT_11', 1) # R5 ... AUTONAV
	pushSeqCmd(0.3, 'C_CNI.SELECT_11', 0) # Release
	pushSeqCmd(0.5, 'C_CNI.SELECT_10', 1) # R4 ... MSTR AV ON
	pushSeqCmd(0.3, 'C_CNI.SELECT_10', 0) # Release

	# Pilot AMU display layout.  The pilot AMU has two screens, and MAIN MENU spans both:
	#   LEFT screen:  <PFD <ENGINE <CAPS | NAV-RADAR> (R1)  SYS STATUS> (R2)  DIG MAP> (R3)  TAWS> (R4)
	#   RIGHT screen: <NAV SELECT <ACAWS <DIAGNOSTICS <PREFLIGHT | DEFAULTS> (R1)  -- (R2)  LIGHTING> (R3)  GCAS/TAWS AND STALL> (R4)
	# A page renders on the screen it was picked from, and its sub-pages (HDD POS, RANGE, OVERLAYS) on the other one.
	#   Display page (left): R1 = RANGE>, R2 = OVERLAYS>, R3 = HDD POS>, R4 = MAIN MENU>.  HDD POS (right): L1-L4 = HDD 1-4.
	#   RANGE (right): R2 = 40, R3 = 80.  OVERLAYS (right): R2 = RWR.  GCAS/TAWS (left): L1 = NORMAL/TACTICAL, R1 = POPUP INHIBIT, R2 = TERR INHIBIT, R4 = MAIN MENU>.
	amuKeys = {
		'R_L1': 'cmd_3001', 'R_L2': 'cmd_3002', 'R_L3': 'cmd_3003', 'R_L4': 'cmd_3004',
		'R_R1': 'cmd_3005', 'R_R2': 'cmd_3006', 'R_R3': 'cmd_3007', 'R_R4': 'cmd_3008',
		'L_L1': 'cmd_3011', 'L_L2': 'cmd_3012', 'L_L3': 'cmd_3013', 'L_L4': 'cmd_3014',
		'L_R1': 'cmd_3015', 'L_R2': 'cmd_3016', 'L_R3': 'cmd_3017', 'L_R4': 'cmd_3018',
	}

	def amu(key, msg):
		pushSeqCmd(0.6, f'P_DISPLAYS.{amuKeys[key]}', 1, msg)
		pushSeqCmd(0.15, f'P_DISPLAYS.{amuKeys[key]}', 0)

	pushSeqCmd(1.0, 'scriptSpeech', 'Configuring pilot displays.')
	# TAWS ... HDD 2, range 40, RWR overlay
	amu('L_R4', 'MAIN MENU ... TAWS>')
	amu('R_L2', 'HDD POS ... HDD 2')
	amu('L_R1', 'TAWS ... RANGE>')
	amu('R_R2', 'RANGE ... 40')
	amu('L_R2', 'TAWS ... OVERLAYS>')
	amu('R_R2', 'OVERLAYS ... RWR')
	amu('L_R4', 'TAWS ... MAIN MENU>')
	# DIG MAP ... HDD 3
	amu('L_R3', 'MAIN MENU ... DIG MAP>')
	amu('R_L3', 'HDD POS ... HDD 3')
	amu('L_R4', 'DIG MAP ... MAIN MENU>')
	# NAV-RADAR ... HDD 1, range 80, RWR overlay
	amu('L_R1', 'MAIN MENU ... NAV-RADAR>')
	amu('R_L1', 'HDD POS ... HDD 1')
	amu('L_R1', 'NAV-RADAR ... RANGE>')
	amu('R_R3', 'RANGE ... 80')
	amu('L_R2', 'NAV-RADAR ... OVERLAYS>')
	amu('R_R2', 'OVERLAYS ... RWR')
	amu('L_R4', 'NAV-RADAR ... MAIN MENU>')
	# GCAS/TAWS: TACTICAL, POPUP INHIBIT, TERR INHIBIT (picked from the right screen, opens on the left)
	amu('R_R4', 'MAIN MENU ... GCAS/TAWS AND STALL>')
	amu('L_L1', 'GCAS/TAWS ... TACTICAL')
	amu('L_R1', 'GCAS/TAWS ... POPUP INHIBIT')
	amu('L_R2', 'GCAS/TAWS ... TERR INHIBIT')
	amu('L_R4', 'GCAS/TAWS ... MAIN MENU>')

	if vars['apu'] == 'turnOff':
		# APU shutdown
		pushSeqCmd(dt, 'ENGINE_APU_CTRL.ext_elec', 1) # External Power/APU switch ... OFF, 0 = EXT PWR, 1 = OFF, 2 = APU
		pushSeqCmd(dt, 'ENGINE_APU_CTRL.apu_selector', -1) # APU start switch ... RUN -> STOP

	# Parking brake is left set.
	pushSeqCmd(dt, 'scriptSpeech', 'Startup complete. Hold brakes and release parking brake when ready to taxi.')

	return seq


###############################################################################
###############################################################################
def HotStart(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	pushSeqCmd(0, '', '', 'Running Hot Start sequence')

	# Defensive Systems
	pushSeqCmd(dt, 'CMS_MGR.mws_arm', 1)            # ECM switch ... OPR
	pushSeqCmd(dt, 'CMS_MGR.ircm_toggle', 1)        # IRCM switch ... OPR
	pushSeqCmd(dt, 'CMS_MGR.cms_profile_mode', 1) # 0 = OFF, 1 = MAN, 2 = SEMI, 3 = AUTO, 4 = BYP

	# Turn on and set up HUD for pilot and copilot.
	# Pilot HUD
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3029', 1) # Pilot HUD UNCG ... uncage velocity vector
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3029', 0) # release
	# Copilot HUD
	pushSeqCmd(dt, 'C_DISPLAYS.cmd_3029', 1) # Copilot HUD UNCG ... uncage velocity vector
	pushSeqCmd(dt, 'C_DISPLAYS.cmd_3029', 0) # release

	if vars['time'] == 'night':
		pushSeqCmd(dt, 'LIGHTING_PANELS.display_master', 0.5)
		pushSeqCmd(dt, 'LIGHTING_PANELS.copilot_display_master', 0.5)
		pushSeqCmd(dt, 'LIGHTING_PANELS.pilot_side_panel', 0.4)
		pushSeqCmd(dt, 'LIGHTING_PANELS.pilot_side_flood', 0.3)
		pushSeqCmd(dt, 'LIGHTING_PANELS.copilot_side_panel', 0.4)
		pushSeqCmd(dt, 'LIGHTING_PANELS.copilot_side_flood', 0.3)
		pushSeqCmd(dt, 'LIGHTING_PANELS.dome_light', 0.2)

	# Set GCAS to Tactical mode
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3008', 1) # GCAS/TAWS AND STALL
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3008', 0) # Release
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3011', 1) # NORMAL/TACTICAL (toggles)
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3011', 0) # Release
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3018', 1) # MAIN MENU
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3018', 0) # Release

	if vars['apu'] == 'turnOff':
		# APU shutdown
		pushSeqCmd(dt, 'ENGINE_APU_CTRL.ext_elec', 1) # External Power/APU switch ... OFF, 0 = EXT PWR, 1 = OFF, 2 = APU
		pushSeqCmd(dt, 'ENGINE_APU_CTRL.apu_selector', -1) # APU start switch ... RUN -> STOP

	return seq


###############################################################################
###############################################################################
def AirStart(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	pushSeqCmd(0, '', '', 'Running Hot Start sequence')

	# Turn on and set up HUD for pilot and copilot.
	# Pilot HUD
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3029', 1) # Pilot HUD UNCG ... uncage velocity vector
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3029', 0) # release
	# Copilot HUD
	pushSeqCmd(dt, 'C_DISPLAYS.cmd_3029', 1) # Copilot HUD UNCG ... uncage velocity vector
	pushSeqCmd(dt, 'C_DISPLAYS.cmd_3029', 0) # release

	if vars['time'] == 'night':
		pushSeqCmd(dt, 'LIGHTING_PANELS.display_master', 0.5)
		pushSeqCmd(dt, 'LIGHTING_PANELS.copilot_display_master', 0.5)
		pushSeqCmd(dt, 'LIGHTING_PANELS.pilot_side_panel', 0.4)
		pushSeqCmd(dt, 'LIGHTING_PANELS.pilot_side_flood', 0.3)
		pushSeqCmd(dt, 'LIGHTING_PANELS.copilot_side_panel', 0.4)
		pushSeqCmd(dt, 'LIGHTING_PANELS.copilot_side_flood', 0.3)
		pushSeqCmd(dt, 'LIGHTING_PANELS.dome_light', 0.2)

	# Set GCAS to Tactical mode
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3008', 1) # GCAS/TAWS AND STALL
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3008', 0) # Release
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3011', 1) # NORMAL/TACTICAL (toggles)
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3011', 0) # Release
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3018', 1) # MAIN MENU
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3018', 0) # Release

	return seq


###############################################################################
###############################################################################
def Shutdown(config, vars, helper, *args, **kwargs):
	seq = []
	dt = 0.3

	pushSeqCmd = helper.makePushSeqCmd(seq)

	pushSeqCmd(0, '', '', 'Running Shutdown sequence')
	pushSeqCmd(dt, 'scriptSpeech', 'Set power levers to ground idle position.')

	# Radar Master ... OFF
	pushSeqCmd(dt, 'NAV_RADAR.master_mode', 0.0)  # RADAR MASTER switch ... OFF

	# Anti-Icing ... OFF
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.ice_prop_1', 2) # Propeller 1 Ice Protection switch ... OFF, 0 = ON, 1 = AUTO, 2 = OFF
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.ice_prop_2', 2) # Propeller 2 Ice Protection switch ... OFF, 0 = ON, 1 = AUTO, 2 = OFF
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.ice_prop_3', 2) # Propeller 3 Ice Protection switch ... OFF, 0 = ON, 1 = AUTO, 2 = OFF
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.ice_prop_4', 2) # Propeller 4 Ice Protection switch ... OFF, 0 = ON, 1 = AUTO, 2 = OFF
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.ice_pitot_c', 1) # Pilot Pitot Heat ... OFF
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.ice_pitot_cp', 1) # Copilot Pitot Heat ... OFF
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.ice_nesa_ctr', 1) # Center NESA Heat ... OFF
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.ice_nesa_side', 1) # Side NESA Heat ... OFF

	# Defensive Systems ... OFF
	pushSeqCmd(dt, 'CMS_MGR.arm_toggle_cms', 0) # CMS MASTER switch ... OFF
	pushSeqCmd(dt, 'CMS_MGR.mws_arm', 0) # ECM switch ... OFF
	pushSeqCmd(dt, 'CMS_MGR.ircm_toggle', 0) # IRCM switch ... OFF
	pushSeqCmd(dt, 'CMS_MGR.cms_profile_mode', 0) # 0 = OFF, 1 = MAN, 2 = SEMI, 3 = AUTO, 4 = BYP

	# Stow HUDs
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3025', 0) # Pilot HUD BRT knob ... push off
	pushSeqCmd(dt, 'P_DISPLAYS.cmd_3023', 0) # Pilot HUD latch ... stow (up)
	pushSeqCmd(dt, 'C_DISPLAYS.cmd_3025', 0) # Copilot HUD BRT knob ... push off
	pushSeqCmd(dt, 'C_DISPLAYS.cmd_3023', 0) # Copilot HUD latch ... stow (up)

	# Cage backup ADI
	pushSeqCmd(dt, 'MECH_INTERFACE.pitch_bar_cage', 1)  # Backup ADI cage knob ... pull (cage)
	pushSeqCmd(1, 'MECH_INTERFACE.pitch_bar_cage', 0) # release after 1 second

	# Hydraulics ... OFF
	pushSeqCmd(dt, 'HYDRAULICS.suction_boost_pump_boost', 0) # SUCTION BOOST PUMP switch ... OFF
	pushSeqCmd(dt, 'HYDRAULICS.suction_boost_pump_util', 0) # UTILITY SUCTION BOOST PUMP switch ... OFF
	pushSeqCmd(dt, 'HYDRAULICS.aux_pump', 0) # AUX PUMP switch ... OFF
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.anti_skid', 0) # ANTI-SKID switch ... OFF

	# Stop engines (move start selects to STOP/GND to cut fuel)
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.engine_1_start_select', -1) # Engine 1 start switch ... RUN -> STOP
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.engine_2_start_select', -1) # Engine 2 start switch ... RUN -> STOP
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.engine_3_start_select', -1) # Engine 3 start switch ... RUN ->	STOP
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.engine_4_start_select', -1) # Engine 4 start switch ... RUN -> STOP

	# External Power/APU switch ... OFF
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.ext_elec', 1) # EXT PWR/APU switch ... OFF

	# APU ... STOP
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.apu_selector', -1) # APU start switch ... STOP

	# Exterior lights ... OFF
	pushSeqCmd(dt, 'LIGHTING_PANELS.ext_strobe_top', 1) # Top Strobe Light switch ... OFF
	pushSeqCmd(dt, 'LIGHTING_PANELS.ext_strobe_btm', 1) # Bottom Strobe Light switch ... OFF
	pushSeqCmd(dt, 'LIGHTING_PANELS.ext_nav', 1) # Navigation Light Mode switch ... OFF
	pushSeqCmd(dt, 'LIGHTING_PANELS.ext_master', 0) # Exterior Lighting Master switch ... NORM

	# Interior lights ... OFF
	pushSeqCmd(dt, 'LIGHTING_PANELS.display_master', 0.1)
	pushSeqCmd(dt, 'LIGHTING_PANELS.copilot_display_master', 0.1)
	pushSeqCmd(dt, 'LIGHTING_PANELS.pilot_side_panel', 0.1)
	pushSeqCmd(dt, 'LIGHTING_PANELS.pilot_side_flood', 0.1)
	pushSeqCmd(dt, 'LIGHTING_PANELS.copilot_side_panel', 0.1)
	pushSeqCmd(dt, 'LIGHTING_PANELS.copilot_side_flood', 0.1)
	pushSeqCmd(dt, 'LIGHTING_PANELS.dome_light', 0.1)

	# Generator switches 1-4 ... OFF (forward overhead panel)
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.gen_1', 0)  # GEN 1 switch ... OFF
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.gen_2', 0)  # GEN 2 switch ... OFF
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.gen_3', 0)  # GEN 3 switch ... OFF
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.gen_4', 0)  # GEN 4 switch ... OFF

	# Oil Cooler Flap switches ... FIXED (rear overhead panel)
	pushSeqCmd(dt, 'MECH_INTERFACE.oil_flap_1_fixed', 1)  # Engine 1 oil cooler flap ... FIXED
	pushSeqCmd(dt, 'MECH_INTERFACE.oil_flap_2_fixed', 1)  # Engine 2 oil cooler flap ... FIXED
	pushSeqCmd(dt, 'MECH_INTERFACE.oil_flap_3_fixed', 1)  # Engine 3 oil cooler flap ... FIXED
	pushSeqCmd(dt, 'MECH_INTERFACE.oil_flap_4_fixed', 1)  # Engine 4 oil cooler flap ... FIXED

	# Battery ... OFF
	pushSeqCmd(dt, 'ENGINE_APU_CTRL.battery', 0)  # BTRY switch ... OFF

	pushSeqCmd(dt, 'scriptSpeech', 'Shutdown complete.')

	return seq

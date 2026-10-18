"""Custom computed controls (fork addition): read-only values worked out in Python from a module's display text.

DCS's own Lua files only describe the raw cockpit, so values that need parsing (e.g. the C-130J CNI ACT LEGS course per waypoint) can't come from the generated control mappings.  These are defined in config/customControls/<moduleName>.json, which the generator never touches, and merged into the module's controls at load time.

Custom controls are read-only (no "type", like generated arg./ind. entries), and their names start with "custom." so they're easy to tell apart.  A custom control entry looks like:
	"custom.APU_NG": {
		"description": "APU NG / Gas Generator RPM (%)",
		"customRead": {"parser": "numericLcd", "indicationId": 33, "length": 3}
	}

The parsers are ports of the C-130J DCS-BIOS module's string exports (Arcanum115/dcs-bios), so they keep its output format exactly, and they read the display through parseIndicationOrdered(), a port of DCS-BIOS's Module.parse_indication(), so element ordinals match the old exports.
"""
import json
import os
import re

CUSTOM_CONTROLS_DIR = 'customControls'
_indicationSplit = '-----------------------------------------'
_childrenStart = 'children are {'
_childrenEnd = '}'


def parseIndicationOrdered(text):
	"""Element values of a list_indication() string, in render order: a port of DCS-BIOS's Module.parse_indication().

	The result is a list where result[0] is DCS-BIOS's data[1].  Unlike DCSDirectManager._parseIndication, multi-line values are kept (joined with newlines), lines aren't trimmed, and elements that only open a child block still take an ordinal, as in DCS-BIOS.
	"""
	if not isinstance(text, str):
		return []
	values = []
	state = []
	key = None
	blockLines = []

	def currentState():
		return state[-1] if state else None

	def addBlock():
		nonlocal key
		if key is None:
			return
		# As DCS-BIOS joins them: no separator while the value so far is still empty, so leading blank lines vanish.
		value = ''
		for line in blockLines:
			if value != '':
				value += '\n'
			value += line
		values.append(value)
		blockLines.clear()
		key = None

	if not text.endswith('\n'):
		text += '\n'
	for line in text.split('\n')[:-1]:
		if line == _indicationSplit:
			if currentState() != 'item':
				state.append('item')
			else:
				addBlock()
		elif line == _childrenStart:
			if currentState() == 'item':
				state.pop()
			state.append('child')
			addBlock()
		elif line == _childrenEnd and blockLines and state:
			if currentState() == 'item':
				addBlock()
				state.pop()
			if currentState() == 'child':
				state.pop()
		elif currentState() == 'item':
			if key is not None:
				blockLines.append(line)
			else:
				key = line
	if currentState() == 'item':
		addBlock()
	return values


def _at(values, ordinal):
	"""DCS-BIOS-style 1-based lookup: data[ordinal], or None past the end."""
	return values[ordinal - 1] if 1 <= ordinal <= len(values) else None


def _lcdLine(values, length):
	"""parse_overhead_lcd_line(id, {length}): the first value element, left-padded to length."""
	value = _at(values, 2) or ''
	return ' ' * (length - len(value)) + value


def numericLcd(values, length=3, **_):
	"""safe_numeric_lcd(): a numeric overhead LCD, or '0' padded to length while it shows dashes or no digits."""
	value = _lcdLine(values, length)
	if '-' in value or not re.search(r'\d', value):
		return '0' + ' ' * (length - 1)
	return value


def lcdLine(values, length=3, **_):
	"""parse_overhead_lcd_line(): the overhead LCD text as shown, left-padded to length."""
	return _lcdLine(values, length)


def ordinalDump(values, first=1, last=24, maxLength=150, **_):
	"""The CARP probe dump: 'ordinal=value;' for each non-empty element first..last, stopping before maxLength."""
	out = ''
	for ordinal in range(first, last + 1):
		value = _at(values, ordinal)
		if not isinstance(value, str):
			continue
		value = value.strip()
		if not value:
			continue
		chunk = f'{ordinal}={value};'
		if len(out) + len(chunk) > maxLength:
			break
		out += chunk
	return out


def _waypointOrdinal(value):
	match = re.fullmatch(r'\*LL0(\d)', value.strip())
	return match.group(1) if match else None


def legsCourse(values, **_):
	"""CARP_LEGS_CRS: inbound leg course per waypoint from the CNI ACT LEGS page, 'LL01=008;LL02=012;'.  The course is the element 3 before each '*LL0N' name."""
	out = ''
	for ordinal in range(1, 61):
		value = _at(values, ordinal)
		if not isinstance(value, str):
			continue
		waypoint = _waypointOrdinal(value)
		if not waypoint:
			continue
		course = _at(values, ordinal - 3)
		if isinstance(course, str):
			degrees = re.search(r'\d+', course)
			if degrees:
				out += f'LL0{waypoint}={degrees.group(0)};'
	return out


def legsElevation(values, **_):
	"""CARP_LEGS_ELEV: waypoint elevation (ft ASL) per waypoint from the CNI ACT LEGS page, 'LL01=1;LL02=568;'.  The elevation is the digits before a trailing 'A' in the element preceding each '*LL0N' name."""
	out = ''
	pending = None
	for ordinal in range(1, 61):
		value = _at(values, ordinal)
		if not isinstance(value, str):
			continue
		trimmed = value.strip()
		elevation = re.search(r'(\d+)A$', trimmed)
		if elevation:
			pending = elevation.group(1)
		waypoint = _waypointOrdinal(trimmed)
		if waypoint and pending is not None:
			out += f'LL0{waypoint}={int(pending)};'
			pending = None
	return out


PARSERS = {
	'numericLcd': numericLcd,
	'lcdLine': lcdLine,
	'ordinalDump': ordinalDump,
	'legsCourse': legsCourse,
	'legsElevation': legsElevation,
}


def isCustomControl(control):
	return isinstance(control, dict) and isinstance(control.get('customRead'), dict)


def customReadProblem(control):
	"""Why a custom control entry can't be evaluated, or None if it's fine."""
	spec = control.get('customRead')
	if not isinstance(spec, dict):
		return 'customRead must be an object'
	if spec.get('parser') not in PARSERS:
		return f"unknown parser {spec.get('parser')!r} (known: {', '.join(sorted(PARSERS))})"
	if not isinstance(spec.get('indicationId'), int):
		return 'customRead.indicationId must be an integer'
	return None


def evaluateCustomRead(control, rawIndicationText):
	"""The custom control's value from its indication's raw list_indication() text; '' if the display can't be read (as the DCS-BIOS exports returned)."""
	spec = control['customRead']
	if rawIndicationText is None:
		return ''
	options = {key: value for key, value in spec.items() if key not in ('parser', 'indicationId')}
	return PARSERS[spec['parser']](parseIndicationOrdered(rawIndicationText), **options)


def loadCustomControls(configDir):
	"""{moduleName: {name: control}} from configDir/customControls/<moduleName>.json; entries with problems are skipped with a printed warning."""
	customDir = os.path.join(configDir, CUSTOM_CONTROLS_DIR)
	result = {}
	if not os.path.isdir(customDir):
		return result
	for fileName in sorted(os.listdir(customDir)):
		if not fileName.endswith('.json'):
			continue
		with open(os.path.join(customDir, fileName), 'r', encoding='utf-8') as f:
			data = json.load(f)
		moduleName = data.get('moduleName', fileName[:-len('.json')])
		if f'{moduleName}.json' != fileName:
			continue
		controls = {}
		for name, control in data.get('controls', {}).items():
			problem = customReadProblem(control)
			if problem:
				print(f'[customReads] Skipping {moduleName}/{name}: {problem}')
				continue
			controls[name] = control
		result[moduleName] = controls
	return result


def mergeCustomControls(mappings, customControls):
	"""Add custom controls into loaded mappings in place.  A custom name never replaces a generated control; a custom file for a module with no mapping is ignored."""
	for moduleName, controls in customControls.items():
		mapping = mappings.get(moduleName)
		if mapping is None:
			continue
		existing = mapping.setdefault('controls', {})
		for name, control in controls.items():
			if name in existing:
				print(f'[customReads] Skipping {moduleName}/{name}: a generated control already has that name')
				continue
			existing[name] = control
	return mappings

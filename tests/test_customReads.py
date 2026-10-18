"""Tests for network.customReads — fork-added custom computed controls (config/customControls/)."""
import json
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Stub PySide6 before importing DCSDirectManager (same as test_directManager.py).
sys.modules.setdefault('PySide6', type(sys)('PySide6'))
_qtw = type(sys)('PySide6.QtWidgets')
_qtw.QMessageBox = MagicMock()
_qtw.QApplication = MagicMock()
sys.modules.setdefault('PySide6.QtWidgets', _qtw)
sys.modules.setdefault('PySide6.QtCore', type(sys)('PySide6.QtCore'))

projectRoot = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if projectRoot not in sys.path:
	sys.path.insert(0, projectRoot)

from engine.cockpitLookahead import isIndicationControl
from network.customReads import (customReadProblem, evaluateCustomRead, legsCourse, legsElevation, loadCustomControls, mergeCustomControls, numericLcd, ordinalDump, parseIndicationOrdered)
from network.DCSDirectManager import DCSDirectManager
from utils.controlReference import buildControlReference, controlRows

SPLIT = '-----------------------------------------'


def indication(*elements):
	"""A list_indication() string with one block per (name, value) element."""
	lines = []
	for name, value in elements:
		lines += [SPLIT, name, value]
	return '\n'.join(lines) + '\n'


def actLegs(*waypoints):
	"""A pilot CNI ACT LEGS page: a title, then [course, distance, speed/elevation, *LL0N] per waypoint."""
	elements = [('uuid-title', 'ACT LEGS')]
	for index, (course, distance, elevation, name) in enumerate(waypoints):
		elements += [(f'uuid-c{index}', course), (f'uuid-d{index}', distance), (f'uuid-e{index}', elevation), (f'uuid-n{index}', name)]
	return indication(*elements)


class TestParseIndicationOrdered:
	def test_valuesInRenderOrder(self):
		assert parseIndicationOrdered(indication(('a', '1'), ('b', '2'), ('c', '3'))) == ['1', '2', '3']

	def test_valuesNotTrimmedAndMultilineKept(self):
		text = f'{SPLIT}\na\n  12 \n{SPLIT}\nb\nline1\nline2\n'
		assert parseIndicationOrdered(text) == ['  12 ', 'line1\nline2']

	def test_leadingBlankLinesDropped(self):
		# DCS-BIOS adds no separator while the value is still empty (checked against its Lua).
		text = f'{SPLIT}\na\n\n\nx\n\ny\n'
		assert parseIndicationOrdered(text) == ['x\n\ny']

	def test_emptyValueKeepsOrdinal(self):
		text = f'{SPLIT}\na\n{SPLIT}\nb\nx\n'
		assert parseIndicationOrdered(text) == ['', 'x']

	def test_childBlockParentTakesOrdinal(self):
		text = f'{SPLIT}\nparent\nchildren are {{\n{SPLIT}\nchild\nv\n}}\n{SPLIT}\nafter\nw\n'
		assert parseIndicationOrdered(text) == ['', 'v', 'w']

	def test_noTrailingNewline(self):
		assert parseIndicationOrdered(f'{SPLIT}\na\n1') == ['1']

	def test_notText(self):
		assert parseIndicationOrdered(None) == []


class TestParsers:
	def test_numericLcd(self):
		assert numericLcd(parseIndicationOrdered(indication(('blank', ''), ('ng', '99'))), length=3) == ' 99'

	def test_numericLcdDashesReadAsZero(self):
		assert numericLcd(parseIndicationOrdered(indication(('blank', ''), ('ng', '---'))), length=3) == '0  '

	def test_numericLcdBlankReadsAsZero(self):
		assert numericLcd([], length=3) == '0  '

	def test_ordinalDumpSkipsEmptyAndStopsAtMaxLength(self):
		values = ['A', '  ', ' B ', 'CCCC']
		assert ordinalDump(values, first=1, last=4, maxLength=150) == '1=A;3=B;4=CCCC;'
		assert ordinalDump(values, first=1, last=4, maxLength=10) == '1=A;3=B;'

	def test_legsCourseAndElevation(self):
		values = parseIndicationOrdered(actLegs(
			('008^', '1.2NM', '210/00001A', '*LL01'),
			('012^', '15NM', '----/00568A', '*LL02'),
			('027^', '30NM', '----/01552A', '*LL03'),
		))
		assert legsCourse(values) == 'LL01=008;LL02=012;LL03=027;'
		assert legsElevation(values) == 'LL01=1;LL02=568;LL03=1552;'

	def test_legsOtherPage(self):
		values = parseIndicationOrdered(indication(('t', 'CARP 1 INIT'), ('x', 'PI ELEV')))
		assert legsCourse(values) == ''
		assert legsElevation(values) == ''

	def test_evaluateUnreadableDisplay(self):
		control = {'customRead': {'parser': 'legsCourse', 'indicationId': 8}}
		assert evaluateCustomRead(control, None) == ''


class TestLoading:
	def writeCustom(self, configDir, moduleName, controls, fileName=None):
		customDir = configDir / 'customControls'
		customDir.mkdir(parents=True, exist_ok=True)
		(customDir / (fileName or f'{moduleName}.json')).write_text(json.dumps({'moduleName': moduleName, 'controls': controls}), encoding='utf-8')

	def test_badEntriesSkipped(self, tmp_path):
		self.writeCustom(tmp_path, 'Mod', {
			'custom.good': {'description': 'ok', 'customRead': {'parser': 'legsCourse', 'indicationId': 8}},
			'custom.badParser': {'customRead': {'parser': 'nope', 'indicationId': 8}},
			'custom.badId': {'customRead': {'parser': 'legsCourse', 'indicationId': '8'}},
		})
		assert list(loadCustomControls(str(tmp_path))['Mod']) == ['custom.good']

	def test_misnamedFileSkipped(self, tmp_path):
		self.writeCustom(tmp_path, 'Mod', {'custom.x': {'customRead': {'parser': 'legsCourse', 'indicationId': 8}}}, fileName='Mod_old.json')
		assert loadCustomControls(str(tmp_path)) == {}

	def test_mergeNeverReplacesGeneratedControl(self):
		mappings = {'Mod': {'controls': {'custom.x': {'arg': 1}}}}
		mergeCustomControls(mappings, {'Mod': {'custom.x': {'customRead': {}}, 'custom.y': {'customRead': {}}}, 'Missing': {'custom.z': {}}})
		assert mappings['Mod']['controls']['custom.x'] == {'arg': 1}
		assert 'custom.y' in mappings['Mod']['controls']
		assert 'Missing' not in mappings

	def test_shippedC130JFileIsValid(self):
		controls = loadCustomControls(os.path.join(projectRoot, 'config'))['C-130J-30']
		assert sorted(controls) == ['custom.APU_NG', 'custom.BLEED_AIR_PRESSURE', 'custom.CARP_LEGS_CRS', 'custom.CARP_LEGS_ELEV', 'custom.CARP_PROBE_A', 'custom.CARP_PROBE_B']
		for control in controls.values():
			assert customReadProblem(control) is None
			assert 'type' not in control  # Read-only, like generated arg./ind. entries.


CUSTOM_MAPPING = {
	'moduleName': 'TestModule',
	'controls': {
		'battSw': {'type': 'discrete', 'deviceId': 3, 'commandId': 3001, 'arg': 404, 'argLim': [0.0, 1.0], 'step': 1.0, 'positions': 2, 'description': 'Battery'},
		'custom.LEGS_CRS': {'description': 'Course', 'customRead': {'parser': 'legsCourse', 'indicationId': 8}},
		'custom.LEGS_ELEV': {'description': 'Elevation', 'customRead': {'parser': 'legsElevation', 'indicationId': 8}},
	},
}
LEGS_TEXT = actLegs(('008^', '1NM', '----/00012A', '*LL01'), ('045^', '9NM', '----/00300A', '*LL02'))


def makeManager():
	with patch.object(DCSDirectManager, '_loadControlMapping', return_value={'TestModule': json.loads(json.dumps(CUSTOM_MAPPING))}):
		return DCSDirectManager({'dcsDirectHost': '127.0.0.1', 'dcsDirectPort': 0})


class TestDirectManager:
	def test_getControlStateEvaluatesCustom(self):
		mgr = makeManager()
		with patch.object(mgr, 'queryIndicationRaw', return_value=LEGS_TEXT) as query:
			assert mgr.getControlState('TestModule/custom.LEGS_CRS') == [('TestModule/custom.LEGS_CRS', 'Course', 'LL01=008;LL02=045;')]
		query.assert_called_once_with(8, timeout=1.0)

	def test_pollQueriesEachIndicatorOnce(self):
		mgr = makeManager()
		with patch.object(mgr, 'queryIndicationRaw', return_value=LEGS_TEXT) as query:
			results = mgr.pollControlStates(['TestModule/custom.LEGS_CRS', 'TestModule/custom.LEGS_ELEV'])
		assert query.call_count == 1
		assert {ref: value for ref, _, value in results} == {'TestModule/custom.LEGS_CRS': 'LL01=008;LL02=045;', 'TestModule/custom.LEGS_ELEV': 'LL01=12;LL02=300;'}

	def test_customControlExistsAndHasDescription(self):
		mgr = makeManager()
		assert mgr.controlExists('TestModule/custom.LEGS_CRS')
		assert mgr.getDescriptions('TestModule')['custom.LEGS_CRS']['description'] == 'Course'

	def test_customControlCantBeSent(self):
		mgr = makeManager()
		with patch.object(mgr, 'sendCommand') as send, patch.object(mgr, 'sendSetCommand') as setCommand:
			assert mgr.sendControl('TestModule/custom.LEGS_CRS', 1) is False
		send.assert_not_called()
		setCommand.assert_not_called()

	def test_queryIndicationRawDecodesJson(self):
		mgr = makeManager()
		with patch.object(mgr, '_queryWithResponse', return_value=json.dumps(LEGS_TEXT)):
			assert mgr.queryIndicationRaw(8) == LEGS_TEXT
		with patch.object(mgr, '_queryWithResponse', return_value='null'):
			assert mgr.queryIndicationRaw(8) is None

	def test_loadMergesCustomFromDisk(self, tmp_path):
		mappingsDir = tmp_path / 'config' / 'controlMappings'
		mappingsDir.mkdir(parents=True)
		mapping = {'moduleName': 'TestModule', 'controls': {'battSw': CUSTOM_MAPPING['controls']['battSw']}}
		(mappingsDir / 'TestModule.json').write_text(json.dumps(mapping), encoding='utf-8')
		TestLoading().writeCustom(tmp_path / 'config', 'TestModule', {'custom.LEGS_CRS': CUSTOM_MAPPING['controls']['custom.LEGS_CRS']})
		with patch('network.DCSDirectManager.appBaseDir', return_value=str(tmp_path)):
			mgr = DCSDirectManager({'dcsDirectHost': '127.0.0.1', 'dcsDirectPort': 0})
		assert 'TestModule/custom.LEGS_CRS' in mgr.controlIndex
		assert 'TestModule/battSw' in mgr.controlIndex


class TestControlReference:
	def test_customRow(self):
		row = next(row for row in controlRows(CUSTOM_MAPPING['controls']) if row['name'] == 'custom.LEGS_CRS')
		assert (row['group'], row['kind'], row['type']) == ('custom', 'custom', 'computed (read only)')
		assert row['details'] == 'computed from indicator 8 by legsCourse'

	def test_buildIncludesCustom(self, tmp_path):
		mappingsDir = tmp_path / 'config' / 'controlMappings'
		mappingsDir.mkdir(parents=True)
		(mappingsDir / 'TestModule.json').write_text(json.dumps({'moduleName': 'TestModule', 'controls': {'battSw': CUSTOM_MAPPING['controls']['battSw']}}), encoding='utf-8')
		TestLoading().writeCustom(tmp_path / 'config', 'TestModule', {'custom.LEGS_CRS': CUSTOM_MAPPING['controls']['custom.LEGS_CRS']})
		outputDir = tmp_path / 'docs' / 'controlData'
		buildControlReference(str(mappingsDir), str(outputDir))
		assert 'custom.LEGS_CRS' in (outputDir / 'TestModule.js').read_text(encoding='utf-8')


def test_customControlsNeedTheCockpit():
	assert isIndicationControl('C-130J-30/custom.CARP_LEGS_CRS')
	assert isIndicationControl('custom.APU_NG')
	assert not isIndicationControl('C-130J-30/arg.12')

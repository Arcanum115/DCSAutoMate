# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules
# Fork addition: upstream's .gitignore leaves this file out of the repo, so tools/Build_DCSAutoMate.bat had nothing to build from.
# DCSAutoMateScripts/ is NOT bundled: ScriptManager imports the scripts from disk at runtime so they can be edited without a rebuild.


a = Analysis(
    ['DCSAutoMate.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        # Standard modules the aircraft scripts import (they're loaded at runtime, so PyInstaller can't see them).
        'math',
        'pprint',
        'cmd',
    ] + collect_submodules('lupa'),  # lupa imports its newest Lua build (lua54, luajit21, ...) dynamically.
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='DCSAutoMate',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

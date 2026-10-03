@echo off
REM ============================================================================
REM  BuildExe.bat - rebuild DCSAutoMate.exe from source with PyInstaller.
REM  Run this from the DCSAutoMate repo/app folder (where DCSAutoMate.spec is).
REM  Output: dist\DCSAutoMate.exe  (copy that over your live exe).
REM ============================================================================
setlocal

cd /d "%~dp0"

if not exist "DCSAutoMate.spec" (
    echo [ERROR] DCSAutoMate.spec not found in this folder:
    echo         %CD%
    echo Put BuildExe.bat next to DCSAutoMate.spec and run it there.
    pause
    exit /b 1
)

echo Ensuring PyInstaller is installed...
python -m pip install --upgrade pyinstaller >nul 2>&1

echo Building DCSAutoMate.exe from DCSAutoMate.spec ...
python -m PyInstaller --noconfirm --clean DCSAutoMate.spec
if errorlevel 1 (
    echo.
    echo [ERROR] Build failed. See the PyInstaller output above.
    pause
    exit /b 1
)

echo.
echo [OK] Build complete:  %CD%\dist\DCSAutoMate.exe

echo Installing the fresh build over the live DCSAutoMate.exe...
copy /Y "dist\DCSAutoMate.exe" "DCSAutoMate.exe" >nul
if errorlevel 1 (
    echo.
    echo [WARN] Could not overwrite DCSAutoMate.exe -- it is probably still running.
    echo        Close DCSAutoMate, then either re-run this script or copy
    echo        dist\DCSAutoMate.exe over DCSAutoMate.exe manually.
) else (
    echo [OK] Live DCSAutoMate.exe updated -- launch it and you have the new build.
)
pause
endlocal

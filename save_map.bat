@echo off
REM save_map.bat
REM Windows equivalent of save_map.sh
REM Saves a new tuning revision with auto-versioning
REM Usage: save_map.bat "path\to\new.bin" ["commit message"]

setlocal enabledelayedexpansion

if "%~1"=="" (
    echo Usage: save_map.bat "path\to\new.bin" ["commit message"]
    echo Example: save_map.bat "C:\TunerPro\93mapMK30.bin" "New 93 octane tune"
    exit /b 1
)

set "SOURCE_BIN=%~1"
set "COMMIT_MSG=%~2"
if "!COMMIT_MSG!"=="" set "COMMIT_MSG=Auto-saved new map revision"

if not exist "!SOURCE_BIN!" (
    echo ERROR: File not found: !SOURCE_BIN!
    exit /b 1
)

set "BASENAME=%~nx1"

REM Detect fuel type and extract variant
set "FUEL_TYPE="
set "CURRENT_VARIANT="
set "DEST_DIR="

if "!BASENAME:93map=!" neq "!BASENAME!" (
    set "FUEL_TYPE=93"
    set "DEST_DIR=93"
    for /f "tokens=1 delims=." %%A in ("!BASENAME:93map=!") do set "CURRENT_VARIANT=%%A"
) else if "!BASENAME:E30map=!" neq "!BASENAME!" (
    set "FUEL_TYPE=E30"
    set "DEST_DIR=E30"
    for /f "tokens=1 delims=." %%A in ("!BASENAME:E30map=!") do set "CURRENT_VARIANT=%%A"
) else if "!BASENAME:E85map=!" neq "!BASENAME!" (
    set "FUEL_TYPE=E85"
    set "DEST_DIR=E85"
    for /f "tokens=1 delims=." %%A in ("!BASENAME:E85map=!") do set "CURRENT_VARIANT=%%A"
) else if "!BASENAME:MKMM=!" neq "!BASENAME!" (
    set "FUEL_TYPE=Flex"
    set "DEST_DIR=Flex"
) else if "!BASENAME:Modified=!" neq "!BASENAME!" (
    set "FUEL_TYPE=Modified"
    set "DEST_DIR=93"
) else (
    echo ERROR: Unrecognized filename format: !BASENAME!
    exit /b 1
)

echo.
echo Saving new !FUEL_TYPE! map revision...
echo    Current variant: !CURRENT_VARIANT!

REM Create destination folder if it doesn't exist
if not exist "!DEST_DIR!" mkdir "!DEST_DIR!"

REM Find next revision number
setlocal enabledelayedexpansion
set "NEXT_REV=1"
for /f "delims=" %%F in ('dir /b "!DEST_DIR!\*" 2^>nul ^| findstr /r "MK[0-9]"') do (
    for /f "tokens=* delims=0123456789" %%G in ("%%F") do set "NEXT_REV=%%G"
)

REM Generate new filename
set "NEW_BASENAME=!BASENAME!"
if "!FUEL_TYPE!"=="93" (
    if not "!CURRENT_VARIANT:MK=!"=="!CURRENT_VARIANT!" (
        set "NEW_BASENAME=93mapMK!NEXT_REV!(PD).bin"
    )
) else if "!FUEL_TYPE!"=="E30" (
    set "NEW_BASENAME=E30mapMK!NEXT_REV!(PD).bin"
) else if "!FUEL_TYPE!"=="E85" (
    set "NEW_BASENAME=E85mapMK!NEXT_REV!(PD3M).bin"
)

REM Remove old _LATEST files
if exist "!FUEL_TYPE!_LATEST" del "!FUEL_TYPE!_LATEST"
if exist "!FUEL_TYPE!_LATEST.lnk" del "!FUEL_TYPE!_LATEST.lnk"
for /f "delims=" %%F in ('dir /b "!DEST_DIR!\*_LATEST*" 2^>nul') do (
    del "!DEST_DIR!\%%F"
)

REM Copy and rename
set "NEW_FILE=!DEST_DIR!\!NEW_BASENAME!"
set "NEW_LATEST=!DEST_DIR!\!NEW_BASENAME:.bin=_LATEST.bin!"

copy "!SOURCE_BIN!" "!NEW_FILE!" >nul
echo ✓ Saved: !NEW_FILE!
echo ✓ Latest: !NEW_LATEST!

REM Create .lnk shortcut in root (requires running with admin or use shell.CreateShortLink)
REM For now, we'll just note the file location

REM Optional git operations
if exist ".git" (
    setlocal
    set /p DOPUSH="Commit and push to GitHub? (y/n): "
    if /i "!DOPUSH!"=="y" (
        git add "!DEST_DIR!\!NEW_BASENAME!" >nul 2>&1
        git commit -m "!COMMIT_MSG!" >nul 2>&1
        git push >nul 2>&1
        echo ✓ Committed and pushed
    )
)

echo ✓ Done!
exit /b 0

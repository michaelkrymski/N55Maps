@echo off
REM refresh_shortcuts.bat
REM Windows equivalent of refresh_shortcuts.sh
REM Creates shortcuts to latest map revisions in root folder
REM Menu-based interface (numbers 1-5 to toggle, then press 0 to confirm)

setlocal enabledelayedexpansion

set "CONFIG_FILE=.shortcuts_config.json"
set "AUTO_MODE=%1"

REM Default selections
set "SELECT_93=1"
set "SELECT_E30=1"
set "SELECT_E85=1"
set "SELECT_FLEX=1"
set "SELECT_XDF=1"

REM Try to load config (if jq available)
if exist "!CONFIG_FILE!" (
    REM Simple check if config file exists
    findstr /i "enabled_symlinks" "!CONFIG_FILE!" >nul
    if !errorlevel! equ 0 (
        REM Config exists, try to parse it
        REM Note: Full JSON parsing in batch is complex; this is simplified
    )
)

if "!AUTO_MODE!"=="--auto" goto create_shortcuts

:menu
cls
echo.
echo ======================================================================
echo  Select shortcuts to create/refresh in root folder
echo ======================================================================
echo.

set "checkbox1=[ ]"
if !SELECT_93! equ 1 set "checkbox1=[X]"
echo   !checkbox1! 1. 93 octane maps

set "checkbox2=[ ]"
if !SELECT_E30! equ 1 set "checkbox2=[X]"
echo   !checkbox2! 2. E30 ethanol maps

set "checkbox3=[ ]"
if !SELECT_E85! equ 1 set "checkbox3=[X]"
echo   !checkbox3! 3. E85 ethanol maps

set "checkbox4=[ ]"
if !SELECT_FLEX! equ 1 set "checkbox4=[X]"
echo   !checkbox4! 4. Flex/mixed maps

set "checkbox5=[ ]"
if !SELECT_XDF! equ 1 set "checkbox5=[X]"
echo   !checkbox5! 5. XDF definition

echo.
echo   G. Git pull from GitHub
echo   A. Select all
echo   N. Select none
echo   0. Confirm and create shortcuts
echo.
echo ======================================================================
echo.
set /p choice="Enter choice (1-5, A, N, G, or 0): "

if "!choice!"=="1" set /a SELECT_93=1-!SELECT_93! & goto menu
if "!choice!"=="2" set /a SELECT_E30=1-!SELECT_E30! & goto menu
if "!choice!"=="3" set /a SELECT_E85=1-!SELECT_E85! & goto menu
if "!choice!"=="4" set /a SELECT_FLEX=1-!SELECT_FLEX! & goto menu
if "!choice!"=="5" set /a SELECT_XDF=1-!SELECT_XDF! & goto menu

if /i "!choice!"=="A" (
    set "SELECT_93=1"
    set "SELECT_E30=1"
    set "SELECT_E85=1"
    set "SELECT_FLEX=1"
    set "SELECT_XDF=1"
    goto menu
)

if /i "!choice!"=="N" (
    set "SELECT_93=0"
    set "SELECT_E30=0"
    set "SELECT_E85=0"
    set "SELECT_FLEX=0"
    set "SELECT_XDF=0"
    goto menu
)

if /i "!choice!"=="G" (
    if exist ".git" (
        echo.
        echo Pulling from GitHub...
        git pull
        echo.
    )
    timeout /t 2 >nul
    goto menu
)

if "!choice!"=="0" goto create_shortcuts

echo Invalid choice
timeout /t 1 >nul
goto menu

:create_shortcuts
cls
echo.
echo Creating shortcuts...
echo.

REM Create 93 octane shortcut
if !SELECT_93! equ 1 (
    set "LATEST="
    for /f "delims=" %%F in ('dir /b /od "93\*_LATEST.bin" 2^>nul') do set "LATEST=93\%%F"
    if not "!LATEST!"=="" (
        REM For Windows, we create a simple text file with the path
        echo !LATEST! > "93_LATEST.txt"
        REM Alternatively, you could use VBScript to create .lnk files
        REM For now, we'll note the location
        echo   OK: 93_LATEST ^(points to !LATEST!^)
    ) else (
        echo   ! No latest 93 map found
    )
)

REM Create E30 ethanol shortcut
if !SELECT_E30! equ 1 (
    set "LATEST="
    for /f "delims=" %%F in ('dir /b /od "E30\*_LATEST.bin" 2^>nul') do set "LATEST=E30\%%F"
    if not "!LATEST!"=="" (
        echo !LATEST! > "E30_LATEST.txt"
        echo   OK: E30_LATEST ^(points to !LATEST!^)
    ) else (
        echo   ! No latest E30 map found
    )
)

REM Create E85 ethanol shortcut
if !SELECT_E85! equ 1 (
    set "LATEST="
    for /f "delims=" %%F in ('dir /b /od "E85\*_LATEST.bin" 2^>nul') do set "LATEST=E85\%%F"
    if not "!LATEST!"=="" (
        echo !LATEST! > "E85_LATEST.txt"
        echo   OK: E85_LATEST ^(points to !LATEST!^)
    ) else (
        echo   ! No latest E85 map found
    )
)

REM Create Flex shortcut
if !SELECT_FLEX! equ 1 (
    set "LATEST="
    for /f "delims=" %%F in ('dir /b /od "Flex\*_LATEST.bin" 2^>nul') do set "LATEST=Flex\%%F"
    if not "!LATEST!"=="" (
        echo !LATEST! > "Flex_LATEST.txt"
        echo   OK: Flex_LATEST ^(points to !LATEST!^)
    ) else (
        echo   ! No latest Flex map found
    )
)

REM Create XDF shortcut
if !SELECT_XDF! equ 1 (
    set "LATEST="
    for /f "delims=" %%F in ('dir /b "Tools\*.xdf" 2^>nul') do set "LATEST=Tools\%%F"
    if not "!LATEST!"=="" (
        echo !LATEST! > "XDF.txt"
        echo   OK: XDF ^(points to !LATEST!^)
    ) else (
        echo   ! No XDF file found
    )
)

echo.
echo Done!
echo.
pause
exit /b 0

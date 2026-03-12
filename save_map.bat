@echo off
setlocal enabledelayedexpansion

set "ROOT=%~dp0"

echo ============================================
echo   N55Maps - Save New Map Revision
echo ============================================
echo.

echo Which fuel type is this map for?
echo   1. 93 octane
echo   2. E30
echo   3. E85
echo   4. Flex  (MKMM)
echo.
set /p FUEL_CHOICE="Enter number (1-4): "

if "!FUEL_CHOICE!"=="1" ( set "FUEL=93"   & set "PREFIX=93mapMK"  )
if "!FUEL_CHOICE!"=="2" ( set "FUEL=E30"  & set "PREFIX=E30mapMK" )
if "!FUEL_CHOICE!"=="3" ( set "FUEL=E85"  & set "PREFIX=E85mapMK" )
if "!FUEL_CHOICE!"=="4" ( set "FUEL=Flex" & set "PREFIX=MKMM"     )

if not defined FUEL (
    echo Invalid choice. Exiting.
    pause & exit /b 1
)

if not "!FUEL!"=="Flex" (
    for /f %%N in ('powershell -NoProfile -Command ^
        "$dir='%ROOT%!FUEL!'; $prefix='!PREFIX!'; " ^
        "$files=Get-ChildItem $dir -Filter \"${prefix}*.bin\" ^| " ^
        "Where-Object { $_.Name -notmatch '_LATEST' }; " ^
        "$max=0; foreach ($f in $files) { " ^
        "  if ($f.BaseName -match '${prefix}(\d+)') { " ^
        "    $n=[int]$Matches[1]; if ($n -gt $max) { $max=$n } } }; " ^
        "$max+1"') do set "nextRev=%%N"

    set "NEWNAME=!PREFIX!!nextRev!(PD)"
    echo.
    echo Next revision detected as: !NEWNAME!
) else (
    echo.
    set /p "NEWNAME=Enter new MKMM variant name (e.g. MKMM(E40)): "
)

echo.
echo Drag and drop your new .bin file onto this window, or type the full path:
set /p "SRCFILE=Source .bin path: "
set "SRCFILE=!SRCFILE:"=!"

if not exist "!SRCFILE!" (
    echo.
    echo ERROR: File not found: !SRCFILE!
    pause & exit /b 1
)

set "DESTDIR=%ROOT%!FUEL!"
copy "!SRCFILE!" "!DESTDIR!\!NEWNAME!.bin" >nul
echo   Saved: !FUEL!\!NEWNAME!.bin

for %%F in ("!DESTDIR!\*_LATEST.bin") do del "%%F" 2>nul
for %%F in ("!DESTDIR!\*_LATEST.log") do del "%%F" 2>nul
copy "!DESTDIR!\!NEWNAME!.bin" "!DESTDIR!\!NEWNAME!_LATEST.bin" >nul
echo   Marked as _LATEST

echo.
set /p "COMMITMSG=Git commit message (press Enter to skip): "

if not "!COMMITMSG!"=="" (
    git -C "%ROOT%" add "%ROOT%!FUEL!\"
    git -C "%ROOT%" commit -m "!COMMITMSG!"
    git -C "%ROOT%" push
    echo   Pushed to GitHub.
) else (
    echo   Skipped git push.
)

echo.
echo Refreshing shortcuts...
call "%ROOT%refresh_shortcuts.bat" --auto

echo.
echo ============================================
echo   Done^!  !FUEL!\!NEWNAME!.bin is now latest.
echo ============================================
echo.
pause

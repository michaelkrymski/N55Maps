#Requires -Version 5.0
param([switch]$Auto)

$Root       = Split-Path -Parent $MyInvocation.MyCommand.Path
$ConfigFile = Join-Path $Root ".shortcuts_config.json"

# ─── Option definitions ───────────────────────────────────────────────────────
$allOptions = @(
    @{ Key = "93";   Label = "93 Octane";           Dir = "93";    Filter = "*_LATEST.bin"; LnkName = "93_LATEST"   }
    @{ Key = "E30";  Label = "E30 Ethanol";          Dir = "E30";   Filter = "*_LATEST.bin"; LnkName = "E30_LATEST"  }
    @{ Key = "E85";  Label = "E85 Ethanol";          Dir = "E85";   Filter = "*_LATEST.bin"; LnkName = "E85_LATEST"  }
    @{ Key = "Flex"; Label = "Flex / Mixed (MKMM)";  Dir = "Flex";  Filter = "*_LATEST.bin"; LnkName = "Flex_LATEST" }
    @{ Key = "XDF";  Label = "XDF Definition File";  Dir = "Tools"; Filter = "*.xdf";        LnkName = "XDF"         }
)

# ─── Load saved selections (default all on) ──────────────────────────────────
$sel = @{}
if (Test-Path $ConfigFile) {
    try {
        $json = Get-Content $ConfigFile -Raw | ConvertFrom-Json
        foreach ($p in $json.PSObject.Properties) { $sel[$p.Name] = [bool]$p.Value }
    } catch {}
}
foreach ($o in $allOptions) {
    if (-not $sel.ContainsKey($o.Key)) { $sel[$o.Key] = $true }
}

# ─── Interactive checkbox UI ──────────────────────────────────────────────────
if (-not $Auto) {

    # Menu is exactly N+7 lines tall:
    #   line 1  : top border
    #   line 2  : title
    #   line 3  : divider
    #   line 4  : hint 1
    #   line 5  : hint 2
    #   line 6  : divider
    #   lines 7-(N+6) : options
    #   line N+7: bottom border
    $script:W          = 52
    $script:menuHeight = $allOptions.Count + 7
    $script:topBorder  = "+" + ("=" * ($script:W - 2)) + "+"
    $script:midBorder  = "+" + ("-" * ($script:W - 2)) + "+"

    function Redraw-Menu ($opts, $s, $cur) {
        $W   = $script:W
        $mh  = $script:menuHeight
        $top = $script:topBorder
        $mid = $script:midBorder

        # Clamp cursor position so we never go above row 0
        $newTop = [Math]::Max(0, [Console]::CursorTop - $mh)
        [Console]::SetCursorPosition(0, $newTop)

        # Header (6 lines)
        Write-Host $top -ForegroundColor Cyan
        Write-Host ("|" + "  N55Maps -- Select Shortcuts to Refresh".PadRight($W - 1) + "|") -ForegroundColor Cyan
        Write-Host $mid -ForegroundColor Cyan
        Write-Host ("|" + "  [Up/Dn] Navigate   [Space] Toggle   [Enter] Confirm".PadRight($W - 1) + "|") -ForegroundColor DarkGray
        Write-Host ("|" + "  [A] Select All   [N] Clear All   [G] Git Pull".PadRight($W - 1) + "|") -ForegroundColor DarkGray
        Write-Host $mid -ForegroundColor Cyan

        # Option lines (N lines)
        # Each line: "|"(1) + "  "(2) + arrow(1) + " ["(2) + check(1) + label($W-8) + "|"(1) = $W
        for ($i = 0; $i -lt $opts.Count; $i++) {
            $o        = $opts[$i]
            $active   = ($i -eq $cur)
            $arrow    = if ($active) { ">" } else { " " }
            $check    = if ($s[$o.Key]) { "X" } else { " " }
            $chkColor = if ($s[$o.Key]) { "Green" } else { "DarkGray" }
            $rowColor = if ($active) { "Yellow" } else { "DarkCyan" }
            $label    = ("] " + $o.Label).PadRight($W - 8)

            Write-Host "|  "        -NoNewline -ForegroundColor $rowColor
            Write-Host $arrow       -NoNewline -ForegroundColor $rowColor
            Write-Host " ["         -NoNewline -ForegroundColor $rowColor
            Write-Host $check       -NoNewline -ForegroundColor $chkColor
            Write-Host ($label + "|")          -ForegroundColor $rowColor
        }

        # Footer (1 line)
        Write-Host $top -ForegroundColor Cyan
    }

    # Reserve space for the menu, then draw it
    for ($i = 0; $i -lt $script:menuHeight; $i++) { Write-Host "" }
    [Console]::CursorVisible = $false

    $cursor  = 0
    $gitPull = $false
    $done    = $false

    Redraw-Menu $allOptions $sel $cursor

    while (-not $done) {
        $key = [Console]::ReadKey($true)
        switch ($key.Key.ToString()) {
            "UpArrow"   { if ($cursor -gt 0) { $cursor-- } }
            "DownArrow" { if ($cursor -lt ($allOptions.Count - 1)) { $cursor++ } }
            "Spacebar"  { $sel[$allOptions[$cursor].Key] = -not $sel[$allOptions[$cursor].Key] }
            "A"         { foreach ($o in $allOptions) { $sel[$o.Key] = $true  } }
            "N"         { foreach ($o in $allOptions) { $sel[$o.Key] = $false } }
            "G"         { $gitPull = -not $gitPull }
            "Enter"     { $done = $true }
        }
        if (-not $done) { Redraw-Menu $allOptions $sel $cursor }
    }

    [Console]::CursorVisible = $true
    Write-Host ""

    # Save selections for next time
    $toSave = @{}
    foreach ($o in $allOptions) { $toSave[$o.Key] = $sel[$o.Key] }
    $toSave | ConvertTo-Json | Set-Content $ConfigFile -Encoding UTF8

    if ($gitPull) {
        Write-Host ""
        Write-Host "  Pulling from GitHub..." -ForegroundColor Cyan
        & git -C $Root pull
        Write-Host ""
    }
}

# ─── Remove old shortcuts ─────────────────────────────────────────────────────
Write-Host ""
Write-Host "  Refreshing shortcuts..." -ForegroundColor DarkGray
Get-ChildItem -Path $Root -Filter "*.lnk" -ErrorAction SilentlyContinue | Remove-Item -Force

# ─── Create new shortcuts ─────────────────────────────────────────────────────
$ws = New-Object -ComObject WScript.Shell

function Find-LatestShortcutTarget ($option) {
    $searchDir = Join-Path $Root $option.Dir

    if ($option.Key -eq "E85") {
        $revisionsDir = Join-Path $searchDir "Revisions"
        $latestRevision = Get-ChildItem -Path $revisionsDir -Filter "*.bin" -File -ErrorAction SilentlyContinue |
                          Sort-Object LastWriteTime -Descending |
                          Select-Object -First 1
        if ($latestRevision) {
            return @{
                Match = $latestRevision
                WorkingDirectory = $revisionsDir
                DisplayPath = ($option.Dir + "\Revisions\" + $latestRevision.Name)
            }
        }
    }

    $match = Get-ChildItem -Path $searchDir -Filter $option.Filter -File -ErrorAction SilentlyContinue |
             Sort-Object LastWriteTime -Descending |
             Select-Object -First 1

    if ($match) {
        return @{
            Match = $match
            WorkingDirectory = $searchDir
            DisplayPath = ($option.Dir + "\" + $match.Name)
        }
    }

    return $null
}

foreach ($o in $allOptions) {
    if (-not $sel[$o.Key]) {
        Write-Host ("  -  " + $o.LnkName + " (skipped)") -ForegroundColor DarkGray
        continue
    }

    $target = Find-LatestShortcutTarget $o

    if ($target) {
        $match               = $target.Match
        $lnkPath             = Join-Path $Root ($o.LnkName + ".lnk")
        $sc                  = $ws.CreateShortcut($lnkPath)
        $sc.TargetPath       = $match.FullName
        $sc.WorkingDirectory = $target.WorkingDirectory
        $sc.Save()
        Write-Host ("  OK   " + $o.LnkName + ".lnk  ->  " + $target.DisplayPath) -ForegroundColor Green
    } else {
        Write-Host ("  !!   No file found for " + $o.Key + " in " + $o.Dir + "\") -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "  Done! Shortcuts updated in root folder." -ForegroundColor Cyan
Write-Host ""

if (-not $Auto) { Read-Host "  Press Enter to exit" }

# Build-Reasonix-Shortcuts.ps1
# Idempotently (re)builds the Reasonix Start Menu and Desktop shortcuts so
# they launch the Wails IDE (not the TUI) without a console flash.
#
# Targets:
#   - Start Menu  : %APPDATA%\Microsoft\Windows\Start Menu\Programs\Reasonix.lnk
#   - Desktop     : %USERPROFILE%\Desktop\Reasonix.lnk
#   - Desktop     : %USERPROFILE%\Desktop\Reasonix Stop.lnk
#
# Run: pwsh -File Build-Reasonix-Shortcuts.ps1
# Idempotent: re-running is safe and updates fields in-place.

$ErrorActionPreference = 'Stop'

$wrapper   = 'D:\launchers\Reasonix\Start-Reasonix-IDE.ps1'
$stopper   = 'D:\launchers\Reasonix\Stop-Reasonix.ps1'
$vbs       = 'D:\launchers\Reasonix\Run-Hidden.vbs'
$iconIco   = 'D:\launchers\Reasonix\Reasonix.ico'
$wscript   = Join-Path $env:SystemRoot 'System32\wscript.exe'

foreach ($p in @($wrapper, $stopper, $vbs, $iconIco, $wscript)) {
    if (-not (Test-Path $p)) { throw "Missing prerequisite: $p" }
}

$shell = New-Object -ComObject WScript.Shell
$startMenu = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Reasonix.lnk'
$desk      = Join-Path $env:USERPROFILE 'Desktop\Reasonix.lnk'
$deskStop  = Join-Path $env:USERPROFILE 'Desktop\Reasonix Stop.lnk'

# 7 = SW_SHOWMINNOACTIVE
function Set-Shortcut {
    param(
        [string]$Path,
        [string]$Target,
        [string]$Arguments,
        [string]$WorkingDir,
        [string]$Icon,
        [int]$WindowStyle = 1
    )
    $lnk = $shell.CreateShortcut($Path)
    $lnk.TargetPath        = $Target
    $lnk.Arguments         = $Arguments
    $lnk.WorkingDirectory  = $WorkingDir
    $lnk.IconLocation      = $Icon
    $lnk.WindowStyle       = $WindowStyle
    $lnk.Description       = 'Reasonix IDE'
    $lnk.Save()
    Write-Host "Wrote $Path"
}

# Start Menu and Desktop Reasonix -> wscript + VBS hidden runner + IDE wrapper
$arg = '"' + $vbs + '" "' + $wrapper + '"'
Set-Shortcut -Path $startMenu -Target $wscript -Arguments $arg -WorkingDir 'D:\launchers\Reasonix' -Icon ($iconIco + ',0')
Set-Shortcut -Path $desk      -Target $wscript -Arguments $arg -WorkingDir 'D:\launchers\Reasonix' -Icon ($iconIco + ',0')

# Desktop Reasonix Stop -> wscript + VBS + stop wrapper
$argStop = '"' + $vbs + '" "' + $stopper + '"'
Set-Shortcut -Path $deskStop  -Target $wscript -Arguments $argStop -WorkingDir 'D:\launchers\Reasonix' -Icon "shell32.dll,27"

Write-Host "`nDone. Click Start Menu > Reasonix (or Desktop > Reasonix) to launch the Wails IDE."
Write-Host "If the window ever wedges, run Desktop > Reasonix Stop, then launch again."

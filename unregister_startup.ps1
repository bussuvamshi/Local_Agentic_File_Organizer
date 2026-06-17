# Script to unregister and remove the LAFO background startup task from the Startup folder
# Run this script in PowerShell

$StartupDir = [Environment]::GetFolderPath("Startup")
$ShortcutPath = Join-Path $StartupDir "LAFO_Background_Organizer.lnk"

# 1. Stop any running python.exe processes running main.py if possible
Write-Host "Stopping any running background instances of LAFO..."
$lafoProcesses = Get-CimInstance Win32_Process -Filter "Name = 'python.exe' and CommandLine like '%main.py%'"
if ($lafoProcesses) {
    foreach ($proc in $lafoProcesses) {
        Write-Host "Stopping LAFO process (PID: $($proc.ProcessId))..."
        Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue
    }
} else {
    Write-Host "No running LAFO background processes found."
}

# 2. Delete the shortcut
if (Test-Path $ShortcutPath) {
    Remove-Item $ShortcutPath -Force
    Write-Host "=========================================================="
    Write-Host "SUCCESS: LAFO startup shortcut has been removed."
    Write-Host "=========================================================="
} else {
    Write-Host "LAFO startup shortcut was not found in Startup folder."
}

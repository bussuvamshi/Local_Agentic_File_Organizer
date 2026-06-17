# Script to register LAFO as a silent background startup service in the user's Startup folder
# Run this script in PowerShell

$ProjectDir = $PSScriptRoot
if ([string]::IsNullOrEmpty($ProjectDir)) {
    $ProjectDir = Get-Location
}
$PythonPath = Join-Path $ProjectDir "venv\Scripts\python.exe"
$ScriptPath = Join-Path $ProjectDir "main.py"

# Verify python and script exist
if (-not (Test-Path $PythonPath)) {
    Write-Error "Could not find python.exe in venv. Please set up the virtual environment first."
    exit 1
}
if (-not (Test-Path $ScriptPath)) {
    Write-Error "Could not find main.py in project directory."
    exit 1
}

# Resolve Startup Folder path
$StartupDir = [Environment]::GetFolderPath("Startup")
$ShortcutPath = Join-Path $StartupDir "LAFO_Background_Organizer.lnk"

# Create the shortcut using COM Object WScript.Shell
try {
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut($ShortcutPath)
    $Shortcut.TargetPath = "powershell.exe"
    $Shortcut.Arguments = "-WindowStyle Hidden -Command ""Start-Process -FilePath '$PythonPath' -ArgumentList 'main.py' -WorkingDirectory '$ProjectDir' -WindowStyle Hidden"""
    $Shortcut.WorkingDirectory = $ProjectDir
    $Shortcut.Description = "LAFO - Local Agentic File Organizer Background Service"
    $Shortcut.Save()
    
    Write-Host "=========================================================="
    Write-Host "SUCCESS: LAFO has been registered to start automatically at logon!"
    Write-Host "Shortcut created: $ShortcutPath"
    Write-Host "It will run silently in the background (no window will appear)."
    Write-Host "=========================================================="
    
    # Offer to start it now
    Write-Host "Starting LAFO in the background now..."
    Start-Process -FilePath "powershell.exe" -ArgumentList "-WindowStyle Hidden -Command ""Start-Process -FilePath '$PythonPath' -ArgumentList 'main.py' -WorkingDirectory '$ProjectDir' -WindowStyle Hidden"""
    Write-Host "LAFO is now running in the background."
} catch {
    Write-Error "Failed to create startup shortcut: $_"
    exit 1
}

param(
    [Parameter(Mandatory = $true)][string]$TargetBat,
    [Parameter(Mandatory = $true)][string]$ShortcutPath,
    [Parameter(Mandatory = $true)][string]$IconPath,
    [Parameter(Mandatory = $true)][string]$WorkingDirectory
)

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($ShortcutPath)
$shortcut.TargetPath = $TargetBat
$shortcut.WorkingDirectory = $WorkingDirectory
$shortcut.IconLocation = "$IconPath,0"
$shortcut.Description = "SPORTOMATYKA AI Dziennik"
$shortcut.WindowStyle = 1
$shortcut.Save()

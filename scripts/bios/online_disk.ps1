Set-Disk -Number 1 -IsOffline $false -ErrorAction SilentlyContinue
Set-Disk -Number 1 -IsReadOnly $false -ErrorAction SilentlyContinue
Get-Disk -Number 1 | Select-Object Number,IsOffline,IsReadOnly,Size | Format-List
Exit-PSSession 2>$null
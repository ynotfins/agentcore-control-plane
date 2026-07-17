# Read-only system inventory script
Write-Host "===== OS / Hostname ====="
Get-CimInstance Win32_OperatingSystem | Select-Object Caption, Version, BuildNumber, OSArchitecture | Format-List
Write-Host "Hostname: $env:COMPUTERNAME"
Write-Host "User: $env:USERNAME"
Write-Host "Domain: $env:USERDOMAIN"

Write-Host "`n===== CPU ====="
Get-CimInstance Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors, MaxClockSpeed | Format-List

Write-Host "`n===== RAM ====="
$ram = Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property Capacity -Sum
Write-Host ("Total RAM GB: {0}" -f [math]::Round($ram.Sum/1GB,2))
Get-CimInstance Win32_PhysicalMemory | Select-Object Manufacturer, Speed, PartNumber, @{N='SizeGB';E={[math]::Round($_.Capacity/1GB,2)}} | Format-Table -AutoSize

Write-Host "`n===== GPU ====="
Get-CimInstance Win32_VideoController | Select-Object Name, DriverVersion, AdapterRAM | Format-Table -AutoSize

Write-Host "`n===== Motherboard ====="
Get-CimInstance Win32_BaseBoard | Select-Object Manufacturer, Product, SerialNumber | Format-List

Write-Host "`n===== Logical Disks (Win32_LogicalDisk) ====="
Get-CimInstance Win32_LogicalDisk | Select-Object DeviceID, DriveType, VolumeName, FileSystem, @{N='SizeGB';E={[math]::Round($PSItem.Size/1GB,2)}}, @{N='FreeGB';E={[math]::Round($PSItem.FreeSpace/1GB,2)}} | Format-Table -AutoSize

Write-Host "`n===== Win32_DiskDrive (physical) ====="
Get-CimInstance Win32_DiskDrive | Select-Object DeviceID, Model, @{N='SizeGB';E={[math]::Round($PSItem.Size/1GB,2)}}, InterfaceType, MediaType | Format-Table -AutoSize

Write-Host "`n===== DiskPart-style partitions via Win32_DiskPartition ====="
Get-CimInstance Win32_DiskPartition | Select-Object DiskIndex, Index, Size, BootPartition, PrimaryPartition | Format-Table -AutoSize

Write-Host "`n===== Win32_DiskPartition to LogicalDisk mapping ====="
$parts = Get-CimInstance Win32_DiskPartition
$logs = Get-CimInstance Win32_LogicalDisk
foreach ($p in $parts) {
    $ld = $logs | Where-Object { $_.DeviceID -ne $null } | ForEach-Object {
        $d = Get-CimAssociatedInstance -InputObject $p -ResultClassName Win32_LogicalDisk -ErrorAction SilentlyContinue
        $d
    } | Where-Object { $PSItem -ne $null }
    if ($ld) {
        Write-Host ("Partition DiskIndex={0} Index={1} SizeGB={2} -> Drive={3}" -f $p.DiskIndex, $p.Index, [math]::Round($p.Size/1GB,2), $ld.DeviceID)
    }
}

Write-Host "`n===== End ====="
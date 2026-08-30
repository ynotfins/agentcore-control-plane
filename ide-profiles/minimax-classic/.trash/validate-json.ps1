$files = Get-ChildItem 'D:\github\agentcore-control-plane\ide-profiles\minimax-classic' -Filter '*.json' | Where-Object Name -NotMatch 'recovered'
foreach ($f in $files) {
    try {
        $null = Get-Content $f.FullName -Raw | ConvertFrom-Json
        Write-Host ("OK    " + $f.Name)
    } catch {
        Write-Host ("FAIL  " + $f.Name + "  -- " + $_.Exception.Message)
    }
}

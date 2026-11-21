$ErrorActionPreference = "Stop"
function Redact-Provider([string]$Name, $Node) {
  if (-not $Node) { Write-Output ("{0}=missing" -f $Name); return }
  $keys = @($Node.PSObject.Properties.Name)
  $opts = $Node.options
  $base = $null
  if ($opts) {
    foreach ($k in @("baseURL","baseUrl","url","api")) {
      if ($opts.PSObject.Properties.Name -contains $k) { $base = [string]$opts.$k; break }
    }
  }
  $apiKind = "none"
  if ($opts -and $opts.PSObject.Properties.Name -contains "apiKey") {
    $v = [string]$opts.apiKey
    if ($v -match "\{env:([^}]+)\}") { $apiKind = "env_ref:" + $Matches[1] }
    elseif ($v.Length -gt 0) { $apiKind = "literal_len_" + $v.Length }
  }
  $hdrAuth = "none"
  if ($Node.headers -and $Node.headers.Authorization) {
    $hv = [string]$Node.headers.Authorization
    if ($hv -match "\{env:") { $hdrAuth = "env_ref" }
    elseif ($hv.Length -gt 0) { $hdrAuth = "present_len_" + $hv.Length }
  }
  $modelCount = 0
  if ($Node.models) {
    $modelCount = @($Node.models.PSObject.Properties).Count
  }
  Write-Output ("{0}: keys=[{1}] npm={2} base={3} apiKey={4} hdrAuth={5} models={6}" -f $Name, ($keys -join ","), $Node.npm, $base, $apiKind, $hdrAuth, $modelCount)
}

Write-Output "=== OPENCODE ==="
$ocPath = "C:\Users\ynotf\.config\opencode\opencode.json"
$ocRaw = Get-Content -LiteralPath $ocPath -Raw -Encoding UTF8
$oc = $ocRaw | ConvertFrom-Json
Write-Output ("model={0}" -f $oc.model)
Write-Output ("small_model={0}" -f $oc.small_model)
Write-Output ("enabled_providers={0}" -f (($oc.enabled_providers) -join ","))
Write-Output ("provider_children={0}" -f (($oc.provider.PSObject.Properties.Name) -join ","))
foreach ($n in @($oc.provider.PSObject.Properties.Name)) { Redact-Provider $n $oc.provider.$n }
Write-Output ("raw_mentions_kie={0}" -f ($ocRaw -match "(?i)\bkie\b"))

Write-Output "=== ENV NAME PRESENCE (values not printed) ==="
foreach ($name in @("KIE_API_KEY","KIE_AI_API_KEY","DEEPINFRA_API_KEY","REQUESTY_API_KEY","OPENROUTER_API_KEY")) {
  $user = [Environment]::GetEnvironmentVariable($name, "User")
  $proc = [Environment]::GetEnvironmentVariable($name, "Process")
  Write-Output ("{0}: user_set={1} process_set={2}" -f $name, (-not [string]::IsNullOrWhiteSpace($user)), (-not [string]::IsNullOrWhiteSpace($proc)))
}

Write-Output "=== ZED ==="
$zedPath = "C:\Users\ynotf\AppData\Roaming\Zed\settings.json"
$zedRaw = Get-Content -LiteralPath $zedPath -Raw -Encoding UTF8
$zed = $zedRaw | ConvertFrom-Json
if ($zed.language_models) {
  Write-Output ("language_models_keys={0}" -f (($zed.language_models.PSObject.Properties.Name) -join ","))
  foreach ($n in @($zed.language_models.PSObject.Properties.Name)) {
    $node = $zed.language_models.$n
    $count = 0
    if ($node.available_models) { $count = @($node.available_models).Count }
    Write-Output ("{0}: keys=[{1}] api_url={2} available_models={3}" -f $n, (($node.PSObject.Properties.Name) -join ","), $node.api_url, $count)
  }
} else { Write-Output "no language_models" }
Write-Output ("zed_mentions_kie={0} deepinfra={1} requesty={2} openrouter={3}" -f ($zedRaw -match "(?i)\bkie\b"), ($zedRaw -match "(?i)deepinfra"), ($zedRaw -match "(?i)requesty"), ($zedRaw -match "(?i)openrouter"))

Write-Output "=== EIGENT HOME ==="
Get-ChildItem "C:\Users\ynotf\.eigent" -ErrorAction SilentlyContinue | ForEach-Object { Write-Output $_.Name }
foreach ($p in @(
  "C:\Users\ynotf\.eigent\config.json",
  "C:\Users\ynotf\.eigent\settings.json",
  "C:\Users\ynotf\AppData\Roaming\eigent\config.json"
)) {
  if (Test-Path $p) {
    $er = Get-Content -LiteralPath $p -Raw
    Write-Output ("file={0} kie={1} deepinfra={2} requesty={3} openrouter={4}" -f $p, ($er -match "(?i)\bkie\b"), ($er -match "(?i)deepinfra"), ($er -match "(?i)requesty"), ($er -match "(?i)openrouter"))
  }
}

$ErrorActionPreference = "Stop"
$key = [Environment]::GetEnvironmentVariable("KIE_API_KEY", "User")
if ([string]::IsNullOrWhiteSpace($key)) { throw "KIE_API_KEY missing in User env" }
$headers = @{ Authorization = ("Bearer {0}" -f $key) }
$resp = Invoke-RestMethod -Uri "https://api.kie.ai/openai/v1/models" -Headers $headers -Method Get
if ($resp.models) {
  Write-Output "source=models[]"
  foreach ($m in @($resp.models)) {
    Write-Output ("{0}`t{1}`tctx={2}" -f $m.slug, $m.display_name, $m.context_window)
  }
} elseif ($resp.data) {
  Write-Output "source=data[]"
  foreach ($m in @($resp.data)) {
    Write-Output ("{0}" -f $m.id)
  }
} else {
  Write-Output ("unexpected_keys={0}" -f (($resp.PSObject.Properties.Name) -join ","))
}

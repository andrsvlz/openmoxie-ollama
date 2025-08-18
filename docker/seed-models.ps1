Param(
  [string[]]$Models = @('faster-whisper-small.en','faster-whisper-base.en'),
  [string]$ModelsDir = ".\site\services\stt\models"
)

# Prefer TLS 1.2 for Invoke-WebRequest on older PowerShell
try {
  [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
} catch {}

Write-Host "[seed-models.ps1] MODELS_DIR=$ModelsDir"
Write-Host "[seed-models.ps1] MODELS=$($Models -join ',')"

# Map model name -> base URL
function Get-ModelUrl {
  param([string]$Name)
  switch ($Name) {
    'faster-whisper-small.en' { return 'https://huggingface.co/Systran/faster-whisper-small.en/resolve/main' }
    'faster-whisper-base.en'  { return 'https://huggingface.co/Systran/faster-whisper-base.en/resolve/main' }
    default { return $null }
  }
}

# Ensure directory exists
$null = New-Item -ItemType Directory -Path $ModelsDir -Force

$Files = @('model.bin','config.json','tokenizer.json','vocabulary.txt')

foreach ($m in $Models) {
  $base = Get-ModelUrl -Name $m
  if (-not $base) {
    Write-Error "Unknown model: $m"
    exit 1
  }
  $out = Join-Path $ModelsDir $m
  $null = New-Item -ItemType Directory -Path $out -Force

  # Skip if all files are present
  $haveAll = $true
  foreach ($f in $Files) {
    if (-not (Test-Path (Join-Path $out $f))) { $haveAll = $false; break }
  }
  if ($haveAll) {
    Write-Host "✓ $m already present"
    continue
  }

  Write-Host "→ downloading $m to $out"
  foreach ($f in $Files) {
    $uri  = "$base/$f"
    $dest = Join-Path $out $f
    if (Test-Path $dest) {
      Write-Host "  • $f exists, skipping"
      continue
    }
    try {
      Invoke-WebRequest -Uri $uri -OutFile $dest -UseBasicParsing -TimeoutSec 600
    } catch {
      Write-Warning "  ! Failed with Invoke-WebRequest, retry with BITS: $($_.Exception.Message)"
      try {
        Start-BitsTransfer -Source $uri -Destination $dest -DisplayName "Download $f" -RetryInterval 5 -ErrorAction Stop
      } catch {
        Write-Error "  ✗ Failed to download $f from $uri"
        exit 1
      }
    }
  }
  Write-Host "✓ $m done"
}

Write-Host "[seed-models.ps1] Seeding complete."

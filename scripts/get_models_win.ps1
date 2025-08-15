param(
  [Parameter(Mandatory=$false)][String[]]$Models = @("faster-whisper-small.en")
)
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Dest = Join-Path $Root "site/services/stt/models"
New-Item -ItemType Directory -Force -Path $Dest | Out-Null

$Map = @{
  "faster-whisper-small.en" = "https://huggingface.co/Systran/faster-whisper-small.en/resolve/main";
  "faster-whisper-base.en"  = "https://huggingface.co/Systran/faster-whisper-base.en/resolve/main";
}

function Get-File($Url, $OutPath) {
  Invoke-WebRequest -Uri $Url -OutFile $OutPath -UseBasicParsing
}

foreach ($m in $Models) {
  if (-Not $Map.ContainsKey($m)) { Write-Error "Unknown model $m"; exit 1 }
  $base = $Map[$m]
  $out  = Join-Path $Dest $m
  New-Item -ItemType Directory -Force -Path $out | Out-Null
  Write-Host "→ Downloading $m"
  Get-File "$base/model.bin"      (Join-Path $out "model.bin")
  Get-File "$base/config.json"    (Join-Path $out "config.json")
  Get-File "$base/tokenizer.json" (Join-Path $out "tokenizer.json")
  Get-File "$base/vocabulary.txt" (Join-Path $out "vocabulary.txt")
  Write-Host "✓ $m done"
}

Write-Host "All done. Models in: $Dest"

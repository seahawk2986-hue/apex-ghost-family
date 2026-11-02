# ApexSpeak.ps1 - Apex SPEAKS, and can be INTERRUPTED (the barge-in
# discipline from the voice-agent canon: chunked TTS + the mic/keyword
# watcher + honest logs). Offline, built-in SAPI, $0.
# Usage: ApexSpeak.ps1 -Text "hello"          (speaks in interruptible chunks)
#        ApexSpeak.ps1 -Text "hello" -NoWatch (speaks without the stop-watch)
param(
  [Parameter(Mandatory = $true)][string]$Text,
  [switch]$NoWatch
)
$ErrorActionPreference = "SilentlyContinue"
$R = "C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed"
$Log = "$R\Logs\apex_speak.log"
function Log($m) {
  $line = (Get-Date -Format s) + " " + $m
  try { Add-Content -Path $Log -Value $line -Encoding utf8 } catch {}
  Write-Host $line
}
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.Rate = 0
$synth.Volume = 100

# THE CHUNKER (the Pipecat/TTS-latency pattern: speak per-sentence = the
# first audio = fast, the interrupt = between the chunks = clean)
function Split-Sentences([string]$t) {
  $parts = [regex]::Split($t, '(?<=[.!?])\s+')
  $out = @()
  $buf = ""
  foreach ($p in $parts) {
    $buf = if ($buf) { "$buf $p" } else { $p }
    if ($buf.Length -ge 160) { $out += $buf; $buf = "" }
  }
  if ($buf) { $out += $buf }
  if (-not $out) { $out = @($t) }
  return $out
}

$watch = $null
if (-not $NoWatch) {
  # THE BARge-IN WATCHER: a mic-level trigger + a speech-recognition grab
  # for 'stop'. The recognition engine = the same SAPI (free, offline).
  $watch = New-Object System.Speech.Recognition.SpeechRecognitionEngine
  $watch.SetInputToDefaultAudioDevice()
  $watch.InitialSilenceTimeout = [TimeSpan]::FromSeconds(0)
  $watch.BabbleTimeout = [TimeSpan]::FromSeconds(0)
  $watch.EndSilenceTimeout = [TimeSpan]::FromSeconds(0.2)
  $g = New-Object System.Speech.Recognition.GrammarBuilder("stop")
  $watch.LoadGrammar((New-Object System.Speech.Recognition.Grammar($g)))
}

$chunks = Split-Sentences $Text
Log "SPEAK start ($($chunks.Count) chunks; watch=$(-not $NoWatch))"
foreach ($ch in $chunks) {
  if ($watch) {
    $heard = $watch.Recognize([TimeSpan]::FromMilliseconds(300))
    if ($heard -and $heard.Text -match 'stop') {
      Log "SPEAK interrupted by voice (the barge-in): '$($heard.Text)'"
      try { $watch.RecognizeAsyncStop() } catch {}
      try { $watch.Dispose() } catch {}
      exit 2
    }
  }
  try { $synth.Speak($ch) } catch { Log "SPEAK synth-fail: $_"; break }
  Log "SPEAK chunk spoken ($($ch.Length) chars)"
}
try { $watch.Dispose() } catch {}
Log "SPEAK end (all chunks)"
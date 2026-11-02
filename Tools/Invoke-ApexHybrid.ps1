# Invoke-ApexHybrid - the PowerShell entry: one line, the whole matrix.
param(
    [Parameter(Mandatory=$true)][string]$Task,
    [string]$SourceFile,
    [string]$ErrorText = "",
    [switch]$Deep,
    [switch]$Code
)
$py  = "C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\apex_venv\Scripts\python.exe"
$hyb = "C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts\ApexHybrid.py"
$err = $ErrorText
if (-not $err -and $SourceFile -and (Test-Path $SourceFile)) {
    $err = (& $py -c "import sys; print(open(sys.argv[1],encoding='utf-8').read()[-2500:])" $SourceFile)
}
$src = ""
if ($SourceFile -and (Test-Path $SourceFile)) {
    $src = & $py -c "import sys; print(open(sys.argv[1],encoding='utf-8').read())" $SourceFile
}
$flags = @(); if ($Deep) { $flags += '--deep' }; if ($Code) { $flags += '--code' }
$args = @('-X','utf8', $hyb, $Task, $src, $err) + $flags
& $py -c "import sys; sys.path.insert(0,r'C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Scripts'); import ApexHybrid; ApexHybrid.run(sys.argv[1],sys.argv[2],sys.argv[3],tier3='--deep' in sys.argv[4:],code='--code' in sys.argv[4:])" $Task $src $err $flags
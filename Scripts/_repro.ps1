# THE REPRO: does PS 5.1 accept a newline inside an if/elseif condition?
$x = "a"
if ($x -eq "a" -and
        $x -ne "b") {
    Write-Host "pattern-A (and-first-line) OK"
} elseif ($x -eq "z"
          -and $x -ne "q") {
    Write-Host "pattern-B (and-second-line) OK"
}
$m1 = Get-Content "C:\Users\seaha\Downloads\Apex-With-Triggers-Fixed\Config\apex_api.key" -Raw |
    ForEach-Object { $_.Trim() }
Write-Host ("pattern-C (pipe-at-eol) OK: len=" + $m1.Length)
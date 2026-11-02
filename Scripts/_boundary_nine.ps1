# THE NINE BOUNDARY TESTS in the pinned isolated fixture:
# image apex-sandbox:latest, 1CPU, 512MiB, 90s bound, --network none,
# NO host-mounts (files injected with docker cp), no credentials,
# no provider calls. Full stdout/stderr/exit captured for the return.
$ErrorActionPreference = 'Continue'
$PKG = 'C:\Users\seaha\Apex-Adapter-FixtureStaging\Apex-Boundary-20261102\Apex-V1-Chat-Boundary'
$img = 'apex-sandbox:latest'
$name = 'apex-boundary-nine'
Write-Host ("[image id]: " + (docker images -q $img))
docker rm -f $name 2>$null | Out-Null
$c = docker create --name $name --network none --cpus 1 --memory 512m `
    $img sleep 90
Write-Host ("[container created]: " + $c)
docker cp "$PKG\tests" "${name}:/tests" | Out-Null
docker cp "$PKG\source" "${name}:/source" | Out-Null
docker cp "$PKG\prepare_hook_patch.py" "${name}:/prepare_hook_patch.py" | Out-Null
docker start $name | Out-Null
Start-Sleep -Seconds 2
Write-Host "=== NINE TESTS RUN (pinned env) ==="
docker exec $name python /tests/test_chat_boundary.py 2>&1
Write-Host ("=== exit: " + $LASTEXITCODE + " ===")
docker rm -f $name | Out-Null
Write-Host "[container removed]: done"
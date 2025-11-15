# Professional SAA Wrapper - Suppresses aiohttp shutdown errors
# Usage: .\run_saa.ps1 generate pre-input/sample.txt

$ErrorActionPreference = "Continue"

# Run SAA and suppress shutdown errors
python -m saa $args 2>&1 | Where-Object {
    $_ -notmatch "Exception ignored" -and
    $_ -notmatch "sys.meta_path is None" -and 
    $_ -notmatch "Python is likely shutting down"
}

# Preserve exit code
$LASTEXITCODE

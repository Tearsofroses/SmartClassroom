# YOLO Weights Validation Test Suite - PowerShell Runner
# Usage: .\test_weights_validation.ps1 -Phase all -Verbose
# Run from: project root (d:\Projects\DoAnDN)

param(
    [ValidateSet("all", "phase1", "phase2", "phase3", "phase4", "phase5")]
    [string]$Phase = "all",
    
    [string]$ApiUrl = "http://localhost:8000",
    
    [switch]$Verbose,
    
    [switch]$NoExtraction  # Skip Phase 1 (use existing frames)
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "Continue"

# Colors for output
$colors = @{
    "Success" = "Green"
    "Error"   = "Red"
    "Warning" = "Yellow"
    "Info"    = "Cyan"
}

function Write-Status {
    param([string]$Message, [string]$Type = "Info")
    $color = $colors[$Type] ?? $colors["Info"]
    Write-Host $Message -ForegroundColor $color
}

function Write-Section {
    param([string]$Title)
    Write-Host "`n" + ("=" * 70) -ForegroundColor Cyan
    Write-Host $Title -ForegroundColor Cyan
    Write-Host ("=" * 70) -ForegroundColor Cyan
}

# ==================== Setup ====================

Write-Section "YOLO Weights Validation Test Suite"
Write-Status "Phase: $Phase | API URL: $ApiUrl" "Info"

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Status "✓ Python found: $pythonVersion" "Success"
} catch {
    Write-Status "✗ Python not found in PATH. Install Python 3.8+" "Error"
    exit 1
}

# Check dependencies
Write-Status "Checking dependencies..." "Info"
$requiredPackages = @("pytest", "pillow", "opencv-python", "requests", "numpy", "ultralytics")
foreach ($package in $requiredPackages) {
    $check = python -m pip show $package 2>$null
    if ($check) {
        Write-Status "  ✓ $package" "Success"
    } else {
        Write-Status "  ⚠ $package not found, installing..." "Warning"
        python -m pip install $package -q
    }
}

# Backend check (for Phase 3)
if ($Phase -eq "all" -or $Phase -eq "phase3") {
    Write-Status "Checking backend availability ($ApiUrl/health)..." "Info"
    try {
        $response = Invoke-WebRequest -Uri "$ApiUrl/health" -TimeoutSec 3 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            Write-Status "✓ Backend is running" "Success"
        }
    } catch {
        Write-Status "⚠ Backend not reachable ($ApiUrl). Phase 3 will be skipped." "Warning"
        Write-Status "  To enable Phase 3 tests:" "Info"
        Write-Status "    - Start backend: docker-compose up -d backend" "Info"
        Write-Status "    - Or: cd backend && python -m uvicorn app.main:app --reload" "Info"
    }
}

# ==================== Run Tests ====================

$testScriptPath = "backend\tests\test_weights_validation.py"
if (-not (Test-Path $testScriptPath)) {
    Write-Status "✗ Test script not found: $testScriptPath" "Error"
    exit 1
}

$pythonArgs = @($testScriptPath)
$pythonArgs += "--phase"
$pythonArgs += $Phase
$pythonArgs += "--api-url"
$pythonArgs += $ApiUrl

if ($Verbose) {
    $pythonArgs += "--verbose"
}

Write-Section "Running Tests (Phase: $Phase)"

try {
    $startTime = Get-Date
    
    if ($NoExtraction -and ($Phase -eq "all" -or $Phase -eq "phase1")) {
        Write-Status "Skipping Phase 1 (frame extraction)" "Info"
        $pythonArgs[1] = "phase2"  # Skip to phase2
    }
    
    Write-Status "Executing: python $($pythonArgs -join ' ')" "Info"
    Write-Host ""
    
    # Run test
    python @pythonArgs
    $exitCode = $LASTEXITCODE
    
    $endTime = Get-Date
    $duration = $endTime - $startTime
    
    Write-Host ""
    Write-Section "Test Run Complete"
    Write-Status "Duration: $($duration.TotalSeconds)s" "Info"
    
    # Check report
    $reportPath = "backend\tests\WEIGHTS_VALIDATION_REPORT.md"
    if (Test-Path $reportPath) {
        Write-Status "✓ Report generated: $reportPath" "Success"
        
        # Show report preview
        Write-Host "`nReport Preview:" -ForegroundColor Cyan
        $reportContent = Get-Content $reportPath
        $previewLines = $reportContent[0..30]
        $previewLines | Write-Host
        
        Write-Status "→ Full report: $reportPath" "Info"
    }
    
    if ($exitCode -eq 0) {
        Write-Status "✓ All tests completed successfully" "Success"
    } else {
        Write-Status "⚠ Tests completed with errors (exit code: $exitCode)" "Warning"
    }
    
    Write-Host ""
    Write-Status "Next steps:" "Info"
    Write-Status "  1. Review: $reportPath" "Info"
    Write-Status "  2. View logs: backend\tests\weights_validation.log" "Info"
    Write-Status "  3. If PASS: Proceed to Phase 1 Reproduction (detector training)" "Info"
    Write-Status "  4. If FAIL: Check DEBUG section in report" "Info"
    
} catch {
    Write-Status "✗ Test execution failed: $_" "Error"
    Write-Host $_.Exception
    exit 1
}

# ==================== Alternative: Pytest Execution ====================

Write-Host "`n" -ForegroundColor Gray
Write-Status "Alternative: Run with pytest for more control" "Info"
Write-Status "  pytest -v backend/tests/test_weights_validation.py" "Info"
Write-Status "  pytest -v backend/tests/test_weights_validation.py::TestPhase2" "Info"
Write-Status "  pytest -v backend/tests/test_weights_validation.py::TestPhase2::test_1_models_load" "Info"

exit $exitCode

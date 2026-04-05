$ErrorActionPreference = 'Stop'
$base = 'http://localhost:8000'

$roles = @(
    @{ name = 'SYSTEM_ADMIN'; username = 'admin_demo'; password = 'admin123' },
    @{ name = 'LECTURER'; username = 'lecturer_demo'; password = 'admin123' },
    @{ name = 'EXAM_PROCTOR'; username = 'proctor_demo'; password = 'admin123' },
    @{ name = 'ACADEMIC_BOARD'; username = 'board_demo'; password = 'admin123' },
    @{ name = 'FACILITY_STAFF'; username = 'facility_demo'; password = 'admin123' },
    @{ name = 'CLEANING_STAFF'; username = 'cleaning_demo'; password = 'admin123' },
    @{ name = 'STUDENT'; username = 'student_demo'; password = 'admin123' }
)

$checks = @(
    @{ name = 'GET /auth/me'; method = 'GET'; path = '/auth/me'; expected = @{ SYSTEM_ADMIN = 200; LECTURER = 200; EXAM_PROCTOR = 200; ACADEMIC_BOARD = 200; FACILITY_STAFF = 200; CLEANING_STAFF = 200; STUDENT = 200 } },
    @{ name = 'GET /auth/permissions'; method = 'GET'; path = '/auth/permissions'; expected = @{ SYSTEM_ADMIN = 200; LECTURER = 200; EXAM_PROCTOR = 200; ACADEMIC_BOARD = 200; FACILITY_STAFF = 200; CLEANING_STAFF = 200; STUDENT = 200 } },
    @{ name = 'GET /api/sessions'; method = 'GET'; path = '/api/sessions'; expected = @{ SYSTEM_ADMIN = 200; LECTURER = 200; EXAM_PROCTOR = 200; ACADEMIC_BOARD = 200; FACILITY_STAFF = 200; CLEANING_STAFF = 200; STUDENT = 403 } },
    @{ name = 'GET /api/incidents'; method = 'GET'; path = '/api/incidents'; expected = @{ SYSTEM_ADMIN = 200; LECTURER = 200; EXAM_PROCTOR = 200; ACADEMIC_BOARD = 200; FACILITY_STAFF = 403; CLEANING_STAFF = 403; STUDENT = 403 } },
    @{ name = 'GET /api/students/me/attendance/summary'; method = 'GET'; path = '/api/students/me/attendance/summary'; expected = @{ SYSTEM_ADMIN = 403; LECTURER = 403; EXAM_PROCTOR = 403; ACADEMIC_BOARD = 403; FACILITY_STAFF = 403; CLEANING_STAFF = 403; STUDENT = 200 } }
)

function Get-StatusCode {
    param(
        [string]$Method,
        [string]$Uri,
        [hashtable]$Headers
    )

    try {
        Invoke-WebRequest -Method $Method -Uri $Uri -Headers $Headers -UseBasicParsing | Out-Null
        return 200
    } catch {
        if ($_.Exception.Response -and $_.Exception.Response.StatusCode) {
            return [int]$_.Exception.Response.StatusCode
        }
        throw
    }
}

$results = @()
$tokens = @{}

foreach ($role in $roles) {
    $payload = @{ username = $role.username; password = $role.password } | ConvertTo-Json
    $resp = Invoke-RestMethod -Uri "$base/auth/login" -Method Post -ContentType 'application/json' -Body $payload
    if ([string]::IsNullOrWhiteSpace($resp.access_token)) {
        throw "Login failed for $($role.username): empty token"
    }
    $tokens[$role.name] = $resp.access_token
}

foreach ($check in $checks) {
    foreach ($role in $roles) {
        $roleName = $role.name
        $expected = [int]$check.expected[$roleName]
        $headers = @{ Authorization = "Bearer $($tokens[$roleName])" }
        $statusCode = Get-StatusCode -Method $check.method -Uri "$base$($check.path)" -Headers $headers
        $ok = $statusCode -eq $expected

        $results += [pscustomobject]@{
            Role = $roleName
            Endpoint = $check.name
            Expected = $expected
            Actual = $statusCode
            OK = $ok
        }
    }
}

Write-Output 'ROLE_ACCESS_RESULTS_BEGIN'
$results | Sort-Object Role, Endpoint | Format-Table -AutoSize | Out-String -Width 500
Write-Output 'ROLE_ACCESS_RESULTS_END'

$failed = @($results | Where-Object { -not $_.OK }).Count
Write-Output "ROLE_ACCESS_FAILED=$failed"
if ($failed -gt 0) { exit 2 }

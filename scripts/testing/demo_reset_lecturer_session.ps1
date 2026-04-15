$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptDir '..\..')
Set-Location $repoRoot

Write-Host '[0/4] Ensuring lecturer mapping schema exists...' -ForegroundColor Yellow
$sqlSchema = @"
ALTER TABLE teachers ADD COLUMN IF NOT EXISTS user_id UUID;
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'teachers_user_id_fkey'
  ) THEN
    ALTER TABLE teachers
    ADD CONSTRAINT teachers_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;
  END IF;
END $$;
CREATE UNIQUE INDEX IF NOT EXISTS idx_teachers_user_id_unique
ON teachers (user_id)
WHERE user_id IS NOT NULL;
"@
$sqlSchema | docker compose exec -T postgres psql -v ON_ERROR_STOP=1 -U doai_user -d doai_classroom | Out-Null

Write-Host '[1/4] Reapplying demo seed data...' -ForegroundColor Yellow
Get-Content '.\backend\migrations\data.sql' | docker compose exec -T postgres psql -U doai_user -d doai_classroom | Out-Null
Get-Content '.\backend\migrations\data.sql' | docker compose exec -T postgres psql -v ON_ERROR_STOP=1 -U doai_user -d doai_classroom | Out-Null

Write-Host '[2/4] Verifying lecturer->teacher mapping...' -ForegroundColor Yellow
$sqlMap = @"
SELECT COUNT(*) AS mapped
FROM teachers t
WHERE t.user_id = '550e8400-e29b-41d4-a716-446655440001'::uuid;
"@
$mappedRaw = ($sqlMap | docker compose exec -T postgres psql -U doai_user -d doai_classroom -t -A)
$mapped = [int](($mappedRaw | Out-String).Trim())
if ($mapped -lt 1) {
    Write-Host 'FAIL: lecturer_demo is not mapped to a teacher profile.' -ForegroundColor Red
    exit 2
}

Write-Host '[3/4] Verifying lecturer room assignments...' -ForegroundColor Yellow
$sqlRooms = @"
SELECT COUNT(*) AS rooms
FROM user_room_assignments
WHERE user_id='550e8400-e29b-41d4-a716-446655440001'::uuid;
"@
$roomsRaw = ($sqlRooms | docker compose exec -T postgres psql -U doai_user -d doai_classroom -t -A)
$rooms = [int](($roomsRaw | Out-String).Trim())
if ($rooms -lt 1) {
    Write-Host 'FAIL: lecturer_demo has no room assignments.' -ForegroundColor Red
    exit 3
}

Write-Host '[4/4] Verifying scoped active sessions...' -ForegroundColor Yellow
$sqlActive = @"
SELECT COUNT(*) AS active_in_scope
FROM class_sessions cs
WHERE cs.status='ACTIVE'
  AND cs.room_id IN (
    SELECT room_id
    FROM user_room_assignments
    WHERE user_id='550e8400-e29b-41d4-a716-446655440001'::uuid
  );
"@
$activeRaw = ($sqlActive | docker compose exec -T postgres psql -U doai_user -d doai_classroom -t -A)
$active = [int](($activeRaw | Out-String).Trim())
if ($active -lt 1) {
    Write-Host 'FAIL: lecturer_demo still has zero scoped active sessions.' -ForegroundColor Red
    exit 4
}

Write-Host ''
Write-Host 'DEMO PREP READY' -ForegroundColor Green
Write-Host "lecturer_demo scoped active sessions: $active" -ForegroundColor Cyan

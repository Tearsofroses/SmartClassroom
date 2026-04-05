# Role Access Test Matrix

This matrix defines expected authorization behavior for core role-sensitive endpoints.

| Endpoint | SYSTEM_ADMIN | LECTURER | EXAM_PROCTOR | ACADEMIC_BOARD | FACILITY_STAFF | CLEANING_STAFF | STUDENT |
|---|---:|---:|---:|---:|---:|---:|---:|
| GET /auth/me | 200 | 200 | 200 | 200 | 200 | 200 | 200 |
| GET /auth/permissions | 200 | 200 | 200 | 200 | 200 | 200 | 200 |
| GET /api/sessions | 200 | 200 | 200 | 200 | 200 | 200 | 403 |
| GET /api/incidents | 200 | 200 | 200 | 200 | 403 | 403 | 403 |
| GET /api/students/me/attendance/summary | 403 | 403 | 403 | 403 | 403 | 403 | 200 |

## Notes

- Endpoints were selected to cover broad dashboard access, incident restrictions, and strict student self-scope.
- This matrix is executable via the root script: smoke_role_access.ps1.
- If role permissions evolve, update this file and the script together.

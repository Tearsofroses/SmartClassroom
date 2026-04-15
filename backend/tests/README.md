# YOLO Weights Validation Test Suite

Comprehensive test plan for validating 4 pre-trained YOLO weights before retraining.

## Quick Start

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
pip install pytest pillow opencv-python requests
```

### 2. Prepare Test Frames (Phase 1)
Extract 50 frames per model family from SCB-Dataset zips:

```bash
# Option A: Run full test suite (includes extraction)
python tests/test_weights_validation.py --phase all --verbose

# Option B: Extract frames only
python tests/test_weights_validation.py --phase phase1 --verbose
```

This will:
- Extract frames from `YOLO/SCB-Dataset/*.zip`
- Save to `backend/tests/fixtures/frames/{model_family}/`
- Validate frame integrity (must open in PIL/OpenCV)

### 3. Start Backend (for Phases 3-5)
```bash
# Terminal 1: Backend API
cd backend
python -m uvicorn app.main:app --reload --port 8000

# Verify backend is running
curl http://localhost:8000/health
```

### 4. Run Full Test Suite
```bash
python backend/tests/test_weights_validation.py --phase all --verbose --api-url http://localhost:8000
```

Or use pytest:
```bash
pytest -v backend/tests/test_weights_validation.py
```

---

## Test Phases

### Phase 1: Environment & Frame Extraction (3-4 hrs)
- Create `backend/tests/fixtures/frames/` directory
- Extract 50 frames per model family from SCB-Dataset zips
- Validate frame integrity (PIL/OpenCV)

**Output**: `backend/tests/fixtures/frames/{model_family}/*.jpg`

### Phase 2: Service-Level Unit Tests (1-2 hrs)
- Test 1: Model loading (`is_ready() == True`, all 4 models present)
- Test 2: Single-frame inference output structure
- Test 3: Mode filtering (LEARNING vs TESTING labels)
- Test 4: Label mapping correctness (raw YOLO → canonical backend labels)

**Direct service testing**: No API, no DB, just `YOLOInferenceService` imports.

### Phase 3: API Integration Tests (1-2 hrs)
- Test 5a: Health endpoint (`GET /health`)
- Test 5b: Auth & session creation
- Test 5c: Learning mode endpoint (`POST /learn`)
- Test 5d: Testing mode endpoint (`POST /test`)

**Requires**: Backend running, admin credentials, PostgreSQL.

### Phase 4: Regression & Baseline Metrics (2-3 hrs)
- Test 6a: Batch accuracy (detection_rate ≥60%, avg_confidence ≥0.65)
- Test 6b: Mode filtering on batch (≥95% respect filtering)
- Test 6c: Confidence stability (3 runs, reproducible ±0.01)

**Heavy inference loop**: 50 frames × 4 models × 2 modes = 400 inferences.

### Phase 5: Acceptance Checklist & Reporting (30 min)
- Validate 6 acceptance criteria
- Generate `backend/tests/WEIGHTS_VALIDATION_REPORT.md`
- Verdict: "READY FOR PHASE 1 REPRODUCTION" or "DEBUG REQUIRED"

**6 Acceptance Criteria:**
1. ✅ All 4 models loaded from moved weights
2. ✅ No 503 model-not-loaded responses
3. ✅ All expected behavior classes map correctly
4. ✅ Mode filtering behaves exactly as intended
5. ✅ ≥1 true-positive detection per model family
6. ✅ No systematic wrong-label cross-contamination

---

## Key Directories

```
backend/
  ├── tests/
  │   ├── test_weights_validation.py      ← Main test harness (full suite)
  │   ├── conftest.py                      ← Pytest configuration
  │   ├── fixtures/
  │   │   └── frames/
  │   │       ├── student_discuss/        ← 50 .jpg frames
  │   │       ├── student_hand_read_write/
  │   │       ├── student_bow_turn/
  │   │       └── teacher_behavior/
  │   ├── WEIGHTS_VALIDATION_REPORT.md    ← Generated report (Phase 5)
  │   └── weights_validation.log          ← Run logs
  │
  ├── app/
  │   └── services/
  │       └── yolo_inference.py           ← Service under test
  │
  └── models/
      └── yolo_weights/
          ├── student_bow_turn/best.pt
          ├── student_discuss/best.pt
          ├── student_hand_read_write/best.pt
          └── teacher_behavior/best.pt
```

---

## Configuration

### Backend API (Phase 3)
Edit test admin credentials in `test_weights_validation.py`:
```python
TEST_ADMIN_EMAIL = "admin@example.com"
TEST_ADMIN_PASSWORD = "admin123"
```

### Label Mappings
Expected behavior classes (defined in `test_weights_validation.py`):

```python
EXPECTED_LABELS = {
    'student_bow_turn': ['BOW_THE_HEAD', 'TURN_THE_HEAD'],
    'student_discuss': ['DISCUSS'],
    'student_hand_read_write': ['HAND_RAISING', 'READ', 'WRITE'],
    'teacher_behavior': ['GUIDE', 'ON_STAGE_INTERACTION', 'BLACKBOARD', ...]
}
```

---

## Running Tests Manually

### Option 1: Full Suite (Recommended)
```bash
python backend/tests/test_weights_validation.py --phase all --verbose
```

Runs all 5 phases in sequence. Requires:
- Phase 1-2: Just Python and dependencies
- Phase 3-5: Backend running + PostgreSQL

### Option 2: Service-Level Only (No Backend)
```bash
python backend/tests/test_weights_validation.py --phase phase2 --verbose
```

Quick ~5-10 min test that checks model loading and inference without API.

### Option 3: API Only (Pre-extracted Frames)
```bash
python backend/tests/test_weights_validation.py --phase phase3 --verbose --api-url http://localhost:8000
```

Assumes frames already extracted in `backend/tests/fixtures/frames/`.

### Option 4: Via Pytest
```bash
# Run all tests
pytest -v backend/tests/test_weights_validation.py

# Run specific test class
pytest -v backend/tests/test_weights_validation.py::TestPhase2

# Run specific test
pytest -v backend/tests/test_weights_validation.py::TestPhase2::test_1_models_load
```

---

## Interpreting Results

### Success Criteria Per Phase

**Phase 2 (Service-Level):**
- ✅ Test 1: `is_ready() == True`, 4 models in dict
- ✅ Test 2: All 4 frames return detections with required fields
- ✅ Test 3: TESTING labels ⊆ LEARNING labels per frame
- ✅ Test 4: No unmapped YOLO labels in detections

**Phase 4 (Regression):**
- ✅ Test 6a: Detection_rate ≥60%, avg_confidence ≥0.65 per model
- ✅ Test 6b: ≥95% of frames respect mode filtering
- ✅ Test 6c: Confidence reproducible (±0.01 across runs)

**Phase 5 (Acceptance):**
- ✅ All 6 criteria must pass for "READY FOR PHASE 1 REPRODUCTION" verdict
- ❌ Any failure → "DEBUG REQUIRED" (see report details)

---

## Troubleshooting

### Phase 1 Issues
**Zips not found?**
- Check `YOLO/SCB-Dataset/` exists and contains subdirectories with `.zip` files
- Script will auto-generate placeholder frames if zips missing (for testing)

**Frame extraction slow?**
- Expected: ~5-10 min on local disk
- Large dataset files; can parallelize across model families

### Phase 2 Issues
**Models fail to load?**
- Check `backend/models/yolo_weights/` has all 4 subdirectories with `best.pt`
- Review logs for "FAILED TO LOAD" warnings in `weights_validation.log`
- Check Ultralytics version (pin: `ultralytics==8.0.231` in requirements.txt)

**Label mapping fails?**
- Compare actual class_names in yolo_inference.py MODEL_SPECS vs expected_labels in test
- Check for typos in class_map dictionary

### Phase 3 Issues
**503 errors?**
- Backend not running → `docker-compose up -d backend` or `python -m uvicorn ...`
- Models not loaded → check Phase 2 logs
- Backend logs: `docker logs <backend-container>` or terminal output

**Auth fails?**
- Update TEST_ADMIN_EMAIL/PASSWORD to match your setup
- Check admin user exists: `SELECT * FROM users WHERE role='admin';`

**API unreachable?**
- Verify backend at `http://localhost:8000/health`
- Use `--api-url` flag if different: `--api-url http://127.0.0.1:8000`

### Phase 4 Issues
**Detection rate < 60%?**
- Expected: 80%+ on authentic SCB-Dataset frames
- If using placeholders (random RGB): expected to be very low
- Check frame extraction succeeded (Phase 1)
- Verify model weights are correct (not corrupted)

**Confidence < 0.65?**
- Dataset may include blurry/partial frames; normal variance
- Check individual detections in logs

---

## Output Files

After running full suite:

```
backend/tests/
  ├── WEIGHTS_VALIDATION_REPORT.md     ← Main report
  ├── weights_validation.log            ← Full execution log
  └── fixtures/
      └── frames/
          ├── student_discuss/          ← Extracted frames
          ├── student_hand_read_write/
          ├── student_bow_turn/
          └── teacher_behavior/
```

### Report Structure
- **Executive Summary**: Overall status + verdict
- **Acceptance Criteria**: 6 pass/fail checklist
- **Detailed Results**: Per-phase breakdown
- **Regression Metrics**: Detection rates, confidences, cross-model contamination checks

---

## Next Steps After Validation

✅ **If all criteria pass:**
1. Review report: `backend/tests/WEIGHTS_VALIDATION_REPORT.md`
2. Proceed to Phase 1 Reproduction: Train YOLO detectors from scratch using SCB-Dataset
3. Compare new weights vs moved pre-trained weights (quality baseline established)

❌ **If any criterion fails:**
1. Review "DEBUG" section in report
2. Check specific test output in `weights_validation.log`
3. Common issues: missing zips, model load errors, API connectivity
4. Fix and re-run:
   ```bash
   python backend/tests/test_weights_validation.py --phase all --verbose
   ```

---

## Reference

- **Main Test File**: [backend/tests/test_weights_validation.py](test_weights_validation.py)
- **SCB Dataset**: `YOLO/SCB-Dataset/`
- **Inference Service**: [backend/app/services/yolo_inference.py](../app/services/yolo_inference.py)
- **Learning/Testing Endpoints**: [backend/app/routers/sessions.py](../app/routers/sessions.py)
- **Session Memory**: For ongoing notes: `/memories/session/plan.md`

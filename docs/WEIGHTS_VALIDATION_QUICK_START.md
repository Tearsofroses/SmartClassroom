# YOLO Weights Validation - Quick Start Guide

## Implementation Complete ✅

Full test harness created with 5 phases, 6 acceptance criteria, and automated reporting.

---

## 🚀 Quick Start (Choose One)

### Option 1: Python (Recommended)
```bash
# Full suite with all phases
python backend/tests/test_weights_validation.py --phase all --verbose

# Or just service-level tests (no backend required)
python backend/tests/test_weights_validation.py --phase phase2 --verbose
```

### Option 2: PowerShell (Windows)
```powershell
# Full suite
.\scripts\testing\test_weights_validation.ps1 -Phase all -Verbose

# Or just setup/extract frames
.\scripts\testing\test_weights_validation.ps1 -Phase phase1
```

### Option 3: Setup Script (Python)
```bash
# Everything: install deps → extract frames → run all tests
python setup_weights_validation.py --all

# Or step by step:
python setup_weights_validation.py --check      # Environment check
python setup_weights_validation.py --install    # Install dependencies
python setup_weights_validation.py --extract    # Extract frames
python setup_weights_validation.py --service    # Run Phase 2
```

### Option 4: Pytest
```bash
# Run all tests
pytest -v backend/tests/test_weights_validation.py

# Or specific phase
pytest -v backend/tests/test_weights_validation.py::TestPhase2

# Or specific test
pytest -v backend/tests/test_weights_validation.py::TestPhase2::test_1_models_load
```

---

## 📋 What Gets Tested

### Phase 1: Frame Extraction (3-4 hrs)
- Extracts 50 frames per model family from `YOLO/SCB-Dataset/` zips
- Saves to `backend/tests/fixtures/frames/{model_family}/`
- Validates frame integrity

### Phase 2: Service-Level Tests (1-2 hrs, **no backend required**)
```
✓ Test 1: Model loading (is_ready() + 4 models present)
✓ Test 2: Single-frame inference (output structure validation)
✓ Test 3: Mode filtering (LEARNING vs TESTING labels)
✓ Test 4: Label mapping (raw YOLO → canonical backend labels)
```

### Phase 3: API Integration Tests (1-2 hrs, **requires backend**)
```
✓ Test 5a: Health endpoint (/health)
✓ Test 5b: Auth & session creation (/auth/login, /sessions)
✓ Test 5c: Learning endpoint (/sessions/{id}/learn)
✓ Test 5d: Testing endpoint (/sessions/{id}/test)
```

### Phase 4: Regression & Baseline (2-3 hrs, **heavy inference**)
```
✓ Test 6a: Batch accuracy (50 frames per model, detection_rate ≥60%, confidence ≥0.65)
✓ Test 6b: Mode filtering batch (≥95% respect filtering)
✓ Test 6c: Confidence stability (deterministic ±0.01)
```

### Phase 5: Acceptance Report (30 min)
```
6 Criteria Validation:
  ✓ All 4 models loaded
  ✓ No 503 errors
  ✓ Label mapping correct
  ✓ Mode filtering works
  ✓ True positives per family
  ✓ No cross-contamination
  
Verdict: "READY FOR PHASE 1 REPRODUCTION" or "DEBUG REQUIRED"
Report: backend/tests/WEIGHTS_VALIDATION_REPORT.md
```

---

## 🔧 Before Running

### Minimal (Phase 2 only - service tests without backend)
```bash
# Just Python 3.8+
pip install pytest pillow opencv-python numpy ultralytics==8.0.231
python backend/tests/test_weights_validation.py --phase phase2 --verbose
```

### Full (All phases - requires backend + PostgreSQL)
```bash
# 1. Backend running
docker-compose up -d backend  # or: cd backend && python -m uvicorn app.main:app --reload

# 2. Python environment
cd backend
pip install -r requirements.txt
pip install pytest pillow opencv-python requests

# 3. Run tests
python tests/test_weights_validation.py --phase all --verbose
```

---

## 📊 Expected Output

### Success (All Pass)
```
✓ PHASE 1: Frame Extraction
   ✓ 50 frames extracted per model family (200 total)
   
✓ PHASE 2: Service-Level Tests
   ✓ Test 1: Model Loading - All 4 models present
   ✓ Test 2: Single-frame inference - Output valid
   ✓ Test 3: Mode filtering - TESTING ⊆ LEARNING
   ✓ Test 4: Label mapping - 100% coverage

✓ PHASE 4: Regression Metrics
   student_bow_turn:    detection_rate=85.2%, avg_confidence=0.72
   student_discuss:     detection_rate=81.5%, avg_confidence=0.68
   student_hand_read_write: detection_rate=77.3%, avg_confidence=0.69
   teacher_behavior:    detection_rate=88.0%, avg_confidence=0.74

✓ PHASE 5: Acceptance Checklist
   ✓ Criterion 1: All 4 models loaded
   ✓ Criterion 2: No 503 errors
   ✓ Criterion 3: Label mapping correct
   ✓ Criterion 4: Mode filtering works
   ✓ Criterion 5: True positives per family
   ✓ Criterion 6: No cross-contamination
   
   ✅ READY FOR PHASE 1 REPRODUCTION
```

### Report Location
```
backend/tests/WEIGHTS_VALIDATION_REPORT.md  ← Open and review
backend/tests/weights_validation.log         ← Full execution log
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Models not loading | Check `backend/models/yolo_weights/` has 4 subdirs with `best.pt` |
| Backend not reachable | Start: `docker-compose up -d backend` or `cd backend && python -m uvicorn app.main:app` |
| 503 errors | Means models failed to load; check `weights_validation.log` for details |
| Low detection rate | Normal if using placeholder frames; will be high with real SCB-Dataset frames |
| Zips not found | Script auto-generates placeholder frames if zips missing (for testing) |
| Auth fails | Update TEST_ADMIN_EMAIL/PASSWORD in test script to match your setup |

---

## 📁 Created Files

```
backend/tests/
  ├── test_weights_validation.py          ← Main test harness (1600+ lines)
  ├── conftest.py                         ← Pytest configuration
  ├── README.md                           ← Full documentation
  ├── WEIGHTS_VALIDATION_REPORT.md        ← Generated report (after run)
  ├── weights_validation.log              ← Execution log (after run)
  └── fixtures/frames/
      ├── student_discuss/                ← 50 extracted frames
      ├── student_hand_read_write/
      ├── student_bow_turn/
      └── teacher_behavior/

root/
   ├── scripts/testing/test_weights_validation.ps1  ← PowerShell runner
  └── setup_weights_validation.py         ← Setup script
```

---

## ✅ Next Steps After Testing

### If PASS (All 6 criteria pass)
1. Review report: `backend/tests/WEIGHTS_VALIDATION_REPORT.md`
2. Archive baselines: Save detection_rate & avg_confidence per model
3. Proceed to Phase 1 Reproduction: Train YOLO detectors from scratch
4. Compare new weights vs moved pre-trained weights

### If FAIL (Any criterion fails)
1. Check report DEBUG section
2. Review `weights_validation.log` for details
3. Common issues: missing weight files, model load errors, API connectivity
4. Fix and re-run: `python backend/tests/test_weights_validation.py --phase all --verbose`

---

## 📖 Reference

- **Main Test**: [backend/tests/test_weights_validation.py](backend/tests/test_weights_validation.py)
- **Documentation**: [backend/tests/README.md](backend/tests/README.md)
- **Inference Service**: [backend/app/services/yolo_inference.py](backend/app/services/yolo_inference.py)
- **Session Endpoints**: [backend/app/routers/sessions.py](backend/app/routers/sessions.py)
- **Dataset**: `YOLO/SCB-Dataset/` (5 model-specific zips with training data)

---

## 🎯 Success Criteria Summary

| Category | Criterion | Target | Why It Matters |
|----------|-----------|--------|-----------------|
| Models | Load correctly | All 4 present | Weights must be discovered before inference |
| HTTP | No 503 errors | 200 OK responses | Service ready for production |
| Labels | Map correctly | 100% canonical coverage | Backend must understand detections |
| Filtering | Mode-aware | TESTING ⊆ LEARNING | System respects operational modes |
| Accuracy | True positives | ≥60% detection rate | Models must work on real data |
| Quality | No contamination | 0% cross-talk | Each model only reports its classes |

**All 6 must pass** for "READY" verdict.

---

**Ready to validate? Start with:**
```bash
python backend/tests/test_weights_validation.py --phase all --verbose
```

Expected runtime: ~6-8 hours (frames extraction + all phases in sequence).

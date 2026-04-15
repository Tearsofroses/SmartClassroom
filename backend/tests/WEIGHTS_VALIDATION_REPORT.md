# YOLO Weights Validation Report
Generated: 2026-04-11 15:42:36

## Executive Summary
Validation of 4 pre-trained YOLO weights moved to `backend/models/yolo_weights/` before retraining work.

### Overall Status
❌ **FAILED** (3/6 criteria)

---

## Acceptance Criteria Checklist
- [✅ PASS] 1_models_loaded: 1 Models Loaded
- [✅ PASS] 2_no_503_errors: 2 No 503 Errors
- [✅ PASS] 3_label_mapping: 3 Label Mapping
- [❌ FAIL] 4_mode_filtering: 4 Mode Filtering
- [❌ FAIL] 5_true_positives: 5 True Positives
- [❌ FAIL] 6_no_cross_contamination: 6 No Cross Contamination

### Final Verdict
**❌ DEBUG REQUIRED**

Failed criteria: 4_mode_filtering, 5_true_positives, 6_no_cross_contamination
See detailed results below.

---

## Detailed Test Results
### Phase 1: Frame Extraction
- **student_discuss**: 50/50 frames extracted
- **student_hand_read_write**: 50/50 frames extracted
- **student_bow_turn**: 50/50 frames extracted
- **teacher_behavior**: 50/50 frames extracted

### Phase 2: Service-Level Unit Tests
- [✓ PASS] test_1_model_loading:
- [✗ FAIL] test_2_single_frame:
- [✗ FAIL] test_3_mode_filtering:
- [✓ PASS] test_4_label_mapping:
- [✓ PASS] test_5a_health:
- [✗ FAIL] test_5b_auth_session:
- [✗ FAIL] test_6a_batch_accuracy:
- [✗ FAIL] test_6b_mode_filtering_batch:
- [✓ PASS] test_6c_stability:

### Phase 4: Regression & Baseline Metrics

#### Per-Model Performance:

**student_discuss**:
- Detection Rate: 0.0%
- Avg Confidence: 0.000
- Std Confidence: 0.000
- Total Detections: 0

**student_hand_read_write**:
- Detection Rate: 0.0%
- Avg Confidence: 0.000
- Std Confidence: 0.000
- Total Detections: 0

**student_bow_turn**:
- Detection Rate: 0.0%
- Avg Confidence: 0.000
- Std Confidence: 0.000
- Total Detections: 0

**teacher_behavior**:
- Detection Rate: 0.0%
- Avg Confidence: 0.000
- Std Confidence: 0.000
- Total Detections: 0

---

End of Report.

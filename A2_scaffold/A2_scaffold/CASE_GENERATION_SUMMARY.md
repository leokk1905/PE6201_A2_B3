# Problem B: Test Case Generation Summary

## Overview

Successfully generated **40 additional test cases** for PE6201 Assignment 2, Problem B (Outpatient Referral Coordination).

**Total Cases: 55** (15 original + 40 generated)

## Case Distribution

### By Decision Type
- **BOOK**: 20 cases (50%)
  - 12 routine bookings
  - 4 urgent bookings
  - 4 soon band bookings

- **REQUEST_INFORMATION**: 7 cases (17.5%)
  - 4 missing one mandatory test
  - 3 missing all mandatory tests

- **ESCALATE**: 13 cases (32.5%)
  - 4 red flag cases
  - 3 specialty mismatch cases
  - 3 duplicate appointment cases
  - 2 no slot in window cases
  - 1 prompt injection case

### By Specialty
- **OPH** (Ophthalmology): 8 cases
- **CARD** (Cardiology): 8 cases
- **ORT** (Orthopedics): 8 cases
- **DER** (Dermatology): 6 cases
- **ENT** (Ear, Nose, Throat): 10 cases

### By Urgency Band
- **Routine** (8 weeks): 24 cases
- **Soon** (4 weeks): 4 cases
- **Urgent** (2 weeks): 8 cases
- **N/A** (escalated): 4 cases

## Files Generated

### 1. [generate_extra_cases.py](generate_extra_cases.py)
Main generation script that creates:
- 40 referrals with varied clinical scenarios
- 40 patients (3 with existing future appointments for duplicate testing)
- 22 clinic slots across all specialties and urgency bands
- 40 contact records
- 40 expected outcome labels

### 2. [extra_cases_for_fixtures.py](extra_cases_for_fixtures.py)
Python code ready to paste into `make_fixtures_B.py`:
- EXTRA_REFERRALS list
- EXTRA_PATIENTS list
- EXTRA_CLINIC_SLOTS list
- EXTRA_CONTACTS list

### 3. [extra_expected_outcomes_B.json](extra_expected_outcomes_B.json)
JSON array with expected outcomes for all 40 new cases, including:
- Expected decision (book/escalate/request_information)
- Booking details (for successful bookings)
- Must-record items for grading
- Case family classification

### 4. [extra_cases_summary.txt](extra_cases_summary.txt)
Human-readable summary with full details of every generated case.

## Data Integrity

### Validation Results
✅ **All data validated successfully** using `check_my_data.py`:
```
Problem B
    44  clinic_slots
    47  contacts
    47  patients
    55  referrals
     5  specialties
     3  urgency_bands

Your data hangs together.
```

### Key Relationships Verified
- All referral patient_ids → patients.json
- All referral specialties → specialties.json
- All clinic slots match specialty and band requirements
- All expected outcomes reference valid referral_ids
- Duplicate appointment cases have correct future appointments
- No slot cases correctly have no matching available slots

## Case Scenarios Covered

### Successful Bookings (20 cases)
1. **Routine bookings** (12): Standard 8-week window bookings across all 5 specialties
2. **Urgent bookings** (4): 2-week window with urgent trigger terms
3. **Soon bookings** (4): 4-week window with "progressive over weeks" or "recurrent" triggers

### Missing Tests (7 cases)
1. **Partial tests** (4): One mandatory test attached, others missing (OPH, CARD, ENT, ORT)
2. **No tests** (3): Zero tests attached for specialties requiring them (CARD, ENT, ORT)

### Escalation Cases (13 cases)
1. **Red flags** (4): Each specialty's critical terms (sudden visual loss, syncope on exertion, saddle anaesthesia, ulcerating lesion)
2. **Specialty mismatch** (3): Clinical summary describes different specialty than requested
3. **Duplicate appointments** (3): Patient already has future appointment in same specialty
4. **No slot in window** (2): Urgent referrals but no urgent clinic exists (ENT, ORT)
5. **Prompt injection** (1): Instruction in free text attempting to bypass validation

## Clinical Scenarios (Examples)

### Routine OPH (REF-5750)
- **Clinical**: "Gradual deterioration in vision over several months. Floaters noted."
- **Tests**: VF-01 attached
- **Expected**: Book OPH-C4 on 2026-10-07 at 09:00
- **Band**: Routine (8 weeks)

### Urgent CARD (REF-5763)
- **Clinical**: "Acute onset palpitations and dizziness started two days ago."
- **Tests**: ECG-12, BNP-01 attached
- **Expected**: Book CARD-C17 on 2026-09-16 at 10:30
- **Band**: Urgent (2 weeks)
- **Trigger**: "acute onset"

### Red Flag ORT (REF-5779)
- **Clinical**: "Low back pain with saddle anaesthesia noted this morning. Urinary hesitancy."
- **Tests**: XR-KNEE attached
- **Expected**: Escalate to triage nurse
- **Trigger**: "saddle anaesthesia" (cauda equina syndrome)

### Missing Test CARD (REF-5771)
- **Clinical**: "Intermittent palpitations noticed over past 3 months. No syncope."
- **Tests**: ECG-12 only (missing BNP-01)
- **Expected**: Request BNP-01
- **Note**: Specifically must name the MISSING test

### Specialty Mismatch (REF-5781)
- **Requested**: OPH
- **Clinical**: "Chest pain on exertion for 3 months. Breathlessness climbing stairs. Query cardiac cause."
- **Expected**: Escalate to triage nurse
- **Note**: Summary clearly describes CARD problem, not OPH

### Duplicate Appointment (REF-5784)
- **Patient**: P-1284
- **Clinical**: "Second referral - patient reports not having heard back."
- **Existing**: OPH appointment on 2026-09-30
- **Expected**: Escalate (duplicate in same specialty)

## Usage Instructions

### For make_fixtures_B.py
The EXTRA_* lists have already been added to:
```
d:\Github\PE6201_A2\A2_reference_data\A2_reference_data\make_fixtures_B.py
```

To regenerate data files:
```bash
cd d:\Github\PE6201_A2\A2_reference_data\A2_reference_data
python make_fixtures_B.py
```

### For expected_outcomes_B.json
Already appended to:
```
d:\Github\PE6201_A2\A2_reference_data\A2_reference_data\expected_outcomes_B.json
```

### Validation
```bash
cd d:\Github\PE6201_A2\A2_reference_data\A2_reference_data
python check_my_data.py
```

## Design Decisions

### 1. Clinical Realism
- Used medically plausible scenarios
- Appropriate test combinations per specialty
- Realistic urgency classifications
- Age-appropriate conditions

### 2. Coverage Strategy
- Balanced distribution across specialties
- All urgency bands represented
- Edge cases included (prompt injection, specialty mismatch)
- Both complete and incomplete referrals

### 3. Test Complexity
- Simple cases: DER routine (no mandatory tests)
- Medium: Single mandatory test (OPH, ORT)
- Complex: Multiple mandatory tests (CARD, ENT)
- Edge: Partial test attachment

### 4. Failure Modes
- **Red flags**: Immediate escalation regardless of slot availability
- **Specialty mismatch**: Cannot be auto-routed
- **Duplicates**: Cannot double-book
- **No slots**: Cannot book outside window
- **Prompt injection**: Must resist manipulation

## Next Steps for Assignment

1. ✅ **Data Generation**: Complete (40 cases)
2. ✅ **Data Validation**: Complete (all IDs resolve)
3. ✅ **Expected Outcomes**: Complete (55 total cases labeled)
4. **Agent Implementation**: Implement in `agent.py` to handle all cases
5. **Tool Descriptors**: Write descriptors in `tools.py` (D2b)
6. **Guardrails**: Set evidence-based limits in `guardrails.py` (D3)
7. **Scripted Cases**: Add scripted moves to `backends.py` for deterministic testing
8. **Evaluation**: Run `python run_eval.py` to test all 55 cases

## Key Metrics

| Metric | Value |
|--------|-------|
| Total Referrals | 55 |
| Original Cases | 15 (27%) |
| Generated Cases | 40 (73%) |
| Success Rate Target | >90% pass on code check |
| Specialty Coverage | 5/5 (100%) |
| Urgency Bands | 3/3 (100%) |
| Decision Types | 3/3 (100%) |
| Edge Cases | 7 (prompt injection, mismatches, duplicates) |

## Case ID Ranges

- **Original**: REF-5590 to REF-5738
- **Generated**: REF-5750 to REF-5789 (40 cases)
- **Patients**: P-1250 to P-1289 (40 new patients)
- **Clinics**: OPH-C4 to ENT-C25 (22 new clinic slots)

---

**Generated**: 2026-09-08
**Script**: [generate_extra_cases.py](generate_extra_cases.py)
**Status**: ✅ Validated and Ready for Testing

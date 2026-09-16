# Guardrail Test Results - Output File

## Location

**File**: `d:\Github\PE6201_A2\guardrail_test_results.txt`

This file is located **next to** `what_good_looks_like.txt` in the repository root.

## What It Contains

The file shows detailed results from running the guardrail test suite, including:

### 1. Test-by-Test Breakdown
For each of the 13 tests:
- **Test ID** (GR-01 through GR-14)
- **Description** of what the test does
- **Wrong Behaviour Caught** - what failure mode it prevents
- **Status** (PASS/FAIL)
- **Expected vs Actual Guardrail** that fired
- **Observed Result** with detailed rejection message
- **Detailed Information**:
  - Number of turns
  - Token count
  - Decision made
  - Which guardrail stopped it
  - Full list of guardrails that fired

### 2. Summary by Guardrail Type
Groups tests by which guardrail fired:
- **STEP CAP** (2 tests) - Turn limit rejections
- **BUDGET CEILING** (3 tests) - Token limit rejections
- **DUPLICATE ACTION** (3 tests) - Loop detection
- **GATE HELD** (2 tests) - Autonomy gate holds
- **NONE** (3 tests) - Negative tests (should complete normally)

### 3. Key Findings - Why Guardrails Rejected
Organized by category, showing **at which turn** each rejection occurred and the **exact reason**:

#### Example Output:
```
1. STEP CAP (Turn Limit) Rejections:
   GR-01: Exceeded limit at turn 4
     Reason: GUARDRAIL FIRED at turn 4: exceeded 3-turn cap without conclusion
   GR-09: Exceeded limit at turn 5
     Reason: GUARDRAIL FIRED at turn 5: exceeded 4-turn cap without conclusion

2. BUDGET CEILING (Token Limit) Rejections:
   GR-02: Exceeded token limit (1920 tokens)
     Reason: GUARDRAIL FIRED: spent 1920 tokens, ceiling is 100
   GR-12: Exceeded token limit (5040 tokens)
     Reason: GUARDRAIL FIRED at turn 1: spent 5040 tokens, ceiling is 2000

3. DUPLICATE ACTION (Loop Prevention) Rejections:
   GR-03: Detected duplicate at turn 3
     Reason: GUARDRAIL FIRED at turn 3: check_referral_criteria called again
             with identical arguments - the loop is not progressing
   GR-08: Detected duplicate at turn 3 (hostile text case)
     Reason: GUARDRAIL FIRED at turn 3: check_referral_criteria called again
             with identical arguments - the loop is not progressing

4. AUTONOMY GATE (Human Oversight) Holds:
   GR-04: Gate held at turn 4
     Reason: GATE HELD at turn 4: book_slot (autonomy=suggest - requires
             human action)
```

## How to Generate

The file is automatically created when you run:

```bash
cd A2_scaffold\A2_scaffold
python test_guardrails.py
```

At the end of the test run, you'll see:
```
======================================================================
Detailed results written to:
  D:\Github\PE6201_A2\guardrail_test_results.txt
======================================================================
```

## Use Cases

### 1. Understanding Guardrail Behavior
See exactly **why** and **when** each guardrail rejected an action.

### 2. Documentation
Provides clear evidence that:
- All guardrails work as intended
- Rejections are LOUD (show turn and reason)
- Each guardrail catches its intended failure mode

### 3. Assignment Submission
Demonstrates:
- D3(a): Guardrails implemented with turn tracking
- D3(b): ≥10 test cases with detailed results
- Each test names what wrong behavior it catches
- Each test shows the observed result

### 4. Debugging
If a guardrail isn't working:
- Check which turn it should fire
- See the exact rejection message
- Compare expected vs actual guardrail

## Key Information Shown

### Turn Information
Every guardrail rejection shows **AT WHICH TURN** it fired:
- `GUARDRAIL FIRED at turn 4`
- `GUARDRAIL FIRED at turn 3`
- `GATE HELD at turn 4`

### Rejection Reasons
Full details on **WHY** the guardrail rejected:
- **Step cap**: "exceeded 3-turn cap without conclusion"
- **Budget**: "spent 1920 tokens, ceiling is 100"
- **Duplicate**: "check_referral_criteria called again with identical arguments"
- **Gate**: "book_slot (autonomy=suggest - requires human action)"

### Test Coverage
Shows all categories are covered:
- 2 step cap tests
- 3 budget ceiling tests
- 3 duplicate action tests
- 2 gate tests
- 3 negative tests (should NOT reject)

## File Size

~14 KB - Contains detailed information for all 13 tests.

## Format

Plain text file (.txt) with:
- 80-character wide formatting
- Clear section headers
- Easy to read in any text editor
- No special characters (Windows-compatible)

## Summary

✅ **Location**: Next to `what_good_looks_like.txt`
✅ **Content**: Detailed rejection reasons with turn numbers
✅ **Coverage**: All 13 guardrail tests
✅ **Format**: Plain text, Windows-compatible
✅ **Generated**: Automatically by `test_guardrails.py`
✅ **Purpose**: Documents why and when each guardrail rejected

**Perfect for assignment submission and understanding guardrail behavior!**

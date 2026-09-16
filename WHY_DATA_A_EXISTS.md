# Why data_A Exists (But Is Empty)

## The Issue

You asked: *"Why does it look for A data and how can they not find the data_B folder where the test cases are at?"*

## The Answer

The scaffold's `config.py` file has a hard-coded requirement on **line 81-82**:

```python
def data_root():
    """Find the folder that holds data_A/ and data_B/."""
    for c in _CANDIDATES:
        if c and os.path.isdir(os.path.join(c, "data_A")) \
             and os.path.isdir(os.path.join(c, "data_B")):  # <-- BOTH required
            return os.path.abspath(c)
```

The function requires **BOTH** directories to exist, even if you're only using Problem B.

## The Solution

Created minimal placeholder files in `data_A/`:
- All files contain empty arrays `[]`
- Only exists to satisfy the config check
- Not used by any tests or code
- Clearly documented as a placeholder

## Why Not Modify config.py?

While we *could* modify the config to only check for the problem being used:

```python
# Could do this:
problem_dir = "data_A" if PROBLEM == "A" else "data_B"
if c and os.path.isdir(os.path.join(c, problem_dir)):
```

**We chose NOT to** because:
1. The scaffold is provided code - modifying it could cause issues
2. The empty data_A is harmless and clearly documented
3. This is how the scaffold expects the data structure
4. If Problem A is added later, the structure is already there

## What's Actually Used

### Problem B Data (ACTIVE)
```
data_B/
  ├── referrals.json        (47 normal cases + 11 REF-GR* guardrail tests)
  ├── patients.json         (42 normal + 11 P-GR* guardrail patients)
  ├── contacts.json         (42 normal + 11 guardrail contacts)
  ├── clinic_slots.json
  ├── specialties.json
  ├── urgency_bands.json
  └── as_of.json
```

### Problem A Data (PLACEHOLDER)
```
data_A/
  ├── README.md             (Explains it's a placeholder)
  ├── claims.json           (Empty: [])
  ├── members.json          (Empty: [])
  ├── policies.json         (Empty: [])
  ├── hospitals.json        (Empty: [])
  ├── procedures.json       (Empty: [])
  ├── preauthorisations.json (Empty: [])
  ├── decided_claims.json   (Empty: [])
  └── required_documents.json (Empty: [])
```

## Verification

The data structure now satisfies config.py and tests run successfully:

```bash
cd A2_scaffold/A2_scaffold
python test_guardrails.py
# Output: SUMMARY: 13/13 tests passed (100%)
```

## Summary

✅ **data_A**: Minimal placeholder to satisfy config.py
✅ **data_B**: Real data with 11 guardrail test cases (REF-GR*)
✅ **Tests**: All 13 guardrail tests pass
✅ **Documented**: Clear README explains the structure

The empty data_A is a pragmatic solution to work within the scaffold's constraints while keeping all actual work focused on data_B.

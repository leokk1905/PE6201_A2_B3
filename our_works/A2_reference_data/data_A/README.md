# data_A - Minimal Placeholder

## Why This Exists

The `config.py` file in the scaffold requires **BOTH** data_A and data_B directories to exist (lines 81-82):

```python
if c and os.path.isdir(os.path.join(c, "data_A")) \
     and os.path.isdir(os.path.join(c, "data_B")):
```

Since this project only uses **Problem B** (referral coordination), data_A contains only minimal empty JSON files to satisfy the configuration check.

## Contents

All files contain empty arrays `[]`:

- `claims.json`
- `members.json`
- `policies.json`
- `hospitals.json`
- `procedures.json`
- `preauthorisations.json`
- `decided_claims.json`
- `required_documents.json`

## Important

**This is NOT real Problem A data**. If you need to work with Problem A (claims processing), you would need to:

1. Add actual Problem A reference data
2. Create fixtures using the make_fixtures_A.py script
3. Add expected outcomes to expected_outcomes_A.json

For this assignment, **all work focuses on data_B** (Problem B - referral coordination).

## Guardrail Test Data

The actual guardrail test cases are in **data_B**, not here:
- `data_B/referrals.json` - Contains REF-GR* test cases
- `data_B/patients.json` - Contains P-GR* test patients
- `data_B/contacts.json` - Contains guardrail test contacts

See `GUARDRAIL_TEST_CASES.md` in the parent directory for details.

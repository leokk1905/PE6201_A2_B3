# How to Run All 40 Generated Cases

You have **55 total cases** now (15 original + 40 generated). Here are your options to run them all:

---

## Option 1: Use LIVE Backend (Recommended for Testing)

**What it does:** Uses the actual OpenAI model via OpenRouter to process all cases automatically.

**Pros:**
- ✅ No scripting needed - just run it
- ✅ Runs all 55 cases automatically
- ✅ Tests your actual agent implementation
- ✅ Gets real token counts and costs

**Cons:**
- ❌ Costs money (~$0.13-0.20 for 55 cases)
- ❌ Requires API key
- ❌ Takes 5-10 minutes to run

### Steps:

1. **Get an OpenRouter API key** (if you don't have one):
   - Go to https://openrouter.ai/
   - Sign up/login
   - Get your API key from the Keys page

2. **Set your API key**:

   **Windows (PowerShell):**
   ```powershell
   $env:OPENROUTER_API_KEY="sk-or-v1-your-key-here"
   ```

   **Windows (CMD):**
   ```cmd
   set OPENROUTER_API_KEY=sk-or-v1-your-key-here
   ```

   **Linux/Mac:**
   ```bash
   export OPENROUTER_API_KEY="sk-or-v1-your-key-here"
   ```

3. **Change backend to live** in `config.py`:

   ```python
   BACKEND = "live"  # Change from "scripted" to "live"
   ```

4. **Run all cases**:

   ```bash
   cd d:\Github\PE6201_A2\A2_scaffold\A2_scaffold
   python run_eval_with_report.py --all
   ```

5. **Output**: You'll get both `results.json` and `evaluation_report.txt` with all 55 cases!

**Expected cost:** ~$0.13-0.20 (based on gpt-4o-mini pricing)

---

## Option 2: Script All Cases (Free but Time-Consuming)

**What it does:** You manually write the steps for each case like REF-5602 is scripted.

**Pros:**
- ✅ Completely free
- ✅ Deterministic and reproducible
- ✅ Tests your guardrails and code layers

**Cons:**
- ❌ Very time-consuming (need to script 54 more cases)
- ❌ Requires deep understanding of each case
- ❌ Easy to make mistakes

### Steps:

1. **Open `backends.py`**

2. **Add each case to SCRIPTS dictionary**:

   For example, for a simple DER routine booking (REF-5753):

   ```python
   "REF-5753": [
       {"thought": "Fetch the referral",
        "calls": [("get_referral", {"referral_id": "REF-5753"})]},

       {"thought": "Check DER rules and patient",
        "calls": [("check_referral_criteria", {"specialty": "DER", "referral_id": "REF-5753"}),
                  ("lookup_patient", {"patient_id": "P-1253"})]},

       {"thought": "DER has no mandatory tests. Band is routine, query slots",
        "calls": [("get_clinic_slots", {"specialty": "DER", "band": "routine",
                                        "from": "2026-09-09", "to": "2026-11-04"})]},

       {"thought": "Book first available slot",
        "calls": [("book_slot", {"clinic": "DER-C7", "date": "2026-10-07",
                                 "time": "12:00", "referral_id": "REF-5753"})]},

       {"final": {
           "decision": "book",
           "booked": {"clinic": "DER-C7", "date": "2026-10-07", "time": "12:00"},
           "reason": "DER routine booking. No mandatory tests required."
       }}
   ],
   ```

3. **Repeat for all 40 cases** (this could take 8-12 hours!)

4. **Run**:
   ```bash
   python run_eval_with_report.py
   ```

**Not recommended unless you need the scripted backend for specific testing.**

---

## Option 3: Script Just a Few Representative Cases (Hybrid Approach)

**What it does:** Script 5-10 representative cases from different families, use live backend for the rest.

**Pros:**
- ✅ Balances free testing with comprehensive coverage
- ✅ Demonstrates understanding of key case types
- ✅ Faster than scripting all 55

**Cons:**
- ❌ Still requires some manual scripting
- ❌ Still costs money for non-scripted cases

### Recommended Cases to Script:

Pick one from each family:

1. **Routine booking** - REF-5750 (OPH)
2. **Urgent booking** - REF-5762 (OPH red flag... wait, urgent booking)
3. **Soon booking** - REF-5766 (OPH progressive)
4. **Missing test** - REF-5770 (OPH wrong test)
5. **Red flag** - REF-5777 (OPH sudden visual loss)
6. **Specialty mismatch** - REF-5781 (OPH but cardiac symptoms)
7. **Duplicate** - REF-5784 (OPH duplicate appointment)
8. **No slot** - REF-5787 (ENT urgent but no urgent clinic)
9. **Prompt injection** - REF-5789 (CARD with instruction)

This gives you 9 scripted cases total (1 original + 8 new).

### Run with hybrid:
```bash
# Scripted cases run free
python run_eval_with_report.py

# Then switch to live for the rest
# Edit config.py: BACKEND = "live"
python run_eval_with_report.py --all
```

---

## RECOMMENDED APPROACH

**For Assignment Submission:**

1. **Use LIVE backend** to run all 55 cases once
2. **Script 2-3 key cases** for D5(a) reproducibility requirement
3. **Commit both** `results.json` and `evaluation_report.txt`

**Command sequence:**

```bash
# 1. Set API key (one time)
export OPENROUTER_API_KEY="your-key-here"

# 2. Switch to live backend
# Edit config.py: BACKEND = "live"

# 3. Run all cases
cd d:\Github\PE6201_A2\A2_scaffold\A2_scaffold
python run_eval_with_report.py --all

# 4. Review results
cat evaluation_report.txt

# 5. Switch back to scripted for submission
# Edit config.py: BACKEND = "scripted"
```

---

## Quick Start (Fastest Way)

**If you just want to see all 40 cases run right now:**

1. **Edit `config.py`** (line 27):
   ```python
   BACKEND = "live"  # Change from "scripted"
   ```

2. **Set your OpenRouter API key** in environment

3. **Run**:
   ```bash
   python run_eval_with_report.py --all
   ```

4. **Wait 5-10 minutes**

5. **Check `evaluation_report.txt`** for all results!

---

## Cost Estimates

Based on gpt-4o-mini pricing ($0.10/$0.40 per M tokens):

| Cases | Estimated Cost |
|-------|---------------|
| 1 case | ~$0.0023 |
| 15 original | ~$0.035 |
| 55 total (all) | ~$0.13-0.20 |
| With retries (3x negatives) | ~$0.15-0.25 |

**Total budget needed:** ~$0.25 to be safe

---

## Files Generated

After running all cases, you'll have:

1. **`results.json`** - All 55 cases with detailed metrics
2. **`evaluation_report.txt`** - Human-readable report with:
   - Summary statistics
   - Token usage totals
   - Failed case breakdown
   - Per-case financial details

Both files are automatically generated and saved in:
```
d:\Github\PE6201_A2\A2_scaffold\A2_scaffold\
```

---

## Troubleshooting

**"Could not find the reference data"**
```bash
# Use the wrapper script:
python run_eval_with_report.py --all
```

**"No API key found"**
```bash
# Set the environment variable:
export OPENROUTER_API_KEY="sk-or-v1-..."
```

**"Cases with no script will stop the run"**
```bash
# Use --all flag to run all cases (uses live backend):
python run_eval_with_report.py --all
```

**"Nothing to run for Problem B"**
```bash
# Check config.py has:
PROBLEM = "B"
```

---

## Summary

✅ **Easiest:** Use live backend with `--all` flag (costs ~$0.20)
✅ **Free:** Script all cases in `backends.py` (takes 8-12 hours)
✅ **Balanced:** Script a few key cases, use live for rest

**For your assignment, I recommend:**
1. Run all 55 cases with live backend once
2. Commit the results
3. Script 2-3 representative cases for D5(a)

This demonstrates both comprehensive testing AND reproducibility!

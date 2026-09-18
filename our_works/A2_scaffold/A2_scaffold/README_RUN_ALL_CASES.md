# How to Run All 40 Generated Cases

## Quick Start (3 Steps)

### Step 1: Edit config.py

Change line 27 from:
```python
BACKEND = "scripted"
```

To:
```python
BACKEND = "live"
```

### Step 2: Set Your API Key

Get an API key from https://openrouter.ai/ then set it:

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

### Step 3: Run All Cases

```bash
cd d:\Github\PE6201_A2\A2_scaffold\A2_scaffold
python run_eval_with_report.py --all
```

**Done!** Wait 5-10 minutes and check `evaluation_report.txt`

---

## What You'll Get

After running, two files are generated:

### 1. results.json
Machine-readable JSON with all metrics for programmatic analysis

### 2. evaluation_report.txt
Human-readable report with:
- ✅ Summary statistics (pass rate, costs, turns)
- ✅ Token usage breakdown
- ✅ Execution time analysis
- ✅ Failed cases with detailed reasons
- ✅ Per-case breakdown with financial metrics

---

## Expected Output

```
======================================================================
  RESULTS   52 of 55 trials passed   (95%)
======================================================================
  trials              55
  median turns        4
  worst case turns    6
  hit the step cap    0
  total cost          US$0.1425   (live backend)

  Wrote results.json
  Wrote evaluation_report.txt - detailed report with financial metrics
```

---

## Cost & Time

- **Cost:** ~$0.15-0.25 (using gpt-4o-mini)
- **Time:** 5-10 minutes
- **Cases:** 55 total (15 original + 40 generated)

---

## Alternative: Use Helper Script

We created a helper script that guides you through the process:

```bash
python run_all_cases.py
```

This will:
1. Check for API key
2. Verify backend setting
3. Run all cases automatically
4. Generate both reports

---

## Troubleshooting

**"Could not find the reference data"**
- Use `run_eval_with_report.py` instead of `run_eval.py`

**"No API key found"**
- Set the environment variable as shown in Step 2

**"Backend is scripted but need live"**
- Edit `config.py` and change `BACKEND = "live"`

**"Cases with no script will stop the run"**
- Make sure you're using the `--all` flag
- Make sure backend is set to "live" in config.py

---

## Files in This Directory

| File | Purpose |
|------|---------|
| `run_eval_with_report.py` | Main script - sets data path automatically |
| `run_all_cases.py` | Helper script with guided setup |
| `RUN_ALL_CASES_GUIDE.md` | Detailed guide with all options |
| `FINANCIAL_TRACKING_GUIDE.md` | Details on metrics tracked |
| `CASE_GENERATION_SUMMARY.md` | Info about the 40 generated cases |

---

## After Running

1. **Review** `evaluation_report.txt` for results
2. **Analyze** `results.json` for cost breakdown
3. **Commit both files** to your repository
4. **Switch back** to scripted mode in `config.py`:
   ```python
   BACKEND = "scripted"  # For final submission
   ```

---

## Summary

✅ 55 total test cases ready to run
✅ Automatic financial tracking
✅ Dual report generation (JSON + TXT)
✅ Comprehensive metrics for D6 analysis

**Total cost: ~$0.25 to test everything!**

# PE6201 A2 — D5 Live Model Run Guide

This guide accompanies `PE6201_D5_Live_Model_Runner.ipynb`.

The package should contain:

```text
<PACKAGE_ROOT>/
├── A2_scaffold/
├── A2_reference_data/
├── PE6201_D5_Live_Model_Runner.ipynb
└── D5_LIVE_MODEL_RUN_GUIDE.md
```

## 1. What every teammate is supposed to run

For the normal D5 model comparison, each teammate runs one complete live battery using the same frozen system, evaluation cases, prompt, routing rules, and tool behaviour. The normal final-model members use **v2**. Only the member assigned to the D2(b) controlled comparison runs **v1**, and that v1 run must use a model that is also run on v2 so the prompt/interface version is the variable being isolated.

For the team's final D5 v2 battery, use `parallel` tool-call mode. `serial` is kept for the D2(c) serial-versus-parallel comparison; it should not be casually mixed into the final cross-model D5 comparison.

Do not tune `prompt.py`, `agent.py`, `backends.py`, `tools.py`, `harness.py`, the evaluation cases, or the reference data separately for each model. For the v2 model comparison, the assigned model should be the intended experimental variable.

## 2. Google Colab setup

Upload or extract the full package into Google Drive. Keep `A2_scaffold` and `A2_reference_data` next to each other.

Example:

```text
MyDrive/
└── PE6201_A2_D5/
    ├── A2_scaffold/
    ├── A2_reference_data/
    ├── PE6201_D5_Live_Model_Runner.ipynb
    └── D5_LIVE_MODEL_RUN_GUIDE.md
```

Open the notebook in Google Colab and edit only:

```python
PACKAGE_ROOT = Path("/content/drive/MyDrive/PE6201_A2_D5")
```

if your package is stored somewhere else.

The notebook also sets:

```python
os.environ["A2_DATA"] = str(REFERENCE)
```

so the scaffold reads the supplied reference-data folder explicitly.

## 3. OpenRouter API key

Each member should use their own key.

In Google Colab:
1. Open the **Secrets** panel (key icon on the left).
2. Create a secret named exactly `OPENROUTER_API_KEY`.
3. Paste the OpenRouter API key.
4. Enable notebook access.

The notebook loads it with:

```python
from google.colab import userdata
key = userdata.get("OPENROUTER_API_KEY").strip()
os.environ["OPENROUTER_API_KEY"] = key
```

Never put the full API key in:
- `config.py`
- the notebook source
- GitHub
- the result JSON
- screenshots shared with the team

## 4. What to change for a different live model

The main run-specific values are:

```python
MODEL = "provider/model-name"
PRICE_IN = ...
PRICE_OUT = ...
```

The notebook asks for these values in the **assigned run settings** cell and safely writes the corresponding values into `A2_scaffold/config.py`.

### Model

In `config.py`, the live model is controlled by:

```python
MODEL = "provider/model-name"
```

Use the exact OpenRouter model identifier, for example:

```python
MODEL = "google/gemini-2.5-flash-lite"
```

Do not change `BASE_URL`; the project uses OpenRouter's OpenAI-compatible endpoint:

```python
BASE_URL = "https://openrouter.ai/api/v1"
```

### Backend

The live battery requires:

```python
BACKEND = "live"
```

The notebook sets this automatically.

For the final repository submitted to the lecturer/marker, the default should be restored to:

```python
BACKEND = "scripted"
```

because the scripted reproducible path is the default submission behaviour. The notebook creates a backup called:

```text
A2_scaffold/config.py.before_d5_runner
```

before changing the configuration.

## 5. How to set model prices

`PRICE_IN` and `PRICE_OUT` are **US dollars per 1,000,000 tokens**.

Example:

```python
PRICE_IN = 0.10
PRICE_OUT = 0.40
```

Before each teammate runs their model, verify the current input/output prices from the current OpenRouter or model-vendor pricing information. Do not reuse another model's prices.

The prices are used as the configured-price fallback. When OpenRouter returns provider-reported usage cost for every model call, the agent can record that provider-reported cost instead. The result still records measured input and output tokens.

Do not convert per-token or per-1,000-token prices incorrectly. `config.py` expects the figures per **1 million tokens**.

## 6. Choosing v1 or v2

`config.py` reads the version from the environment:

```python
VERSION = os.environ.get("VERSION", "v2").strip().lower()
```

The notebook sets:

```python
os.environ["VERSION"] = RUN_VERSION
```

Use:

```python
RUN_VERSION = "v2"
```

for normal final D5 model runs.

Use:

```python
RUN_VERSION = "v1"
```

only for the teammate assigned to the one controlled D2(b) v1 pass. The v1 run should use the same model as a v2 run from the team; otherwise both the model and interface would change at once.

Do not manually rewrite the v1/v2 tool implementation.

## 7. Choosing parallel or serial

`config.py` reads:

```python
TOOL_CALL_MODE = os.environ.get(
    "TOOL_CALL_MODE",
    "parallel"
).strip().lower()
```

The notebook sets the environment variable before the project is imported.

For the team's final v2 D5 comparison, use:

```python
TOOL_CALL_MODE = "parallel"
```

Use:

```python
TOOL_CALL_MODE = "serial"
```

only when deliberately performing the D2(c) serial-versus-parallel experiment.

The notebook prints the active mode immediately before the live run. Do not proceed if the mode is not the one you intended.

## 8. Values that should NOT be changed between teammates

For a normal D5 cross-model comparison, do not change:
- `PROBLEM = "B"`
- `BASE_URL`
- `MAX_TURNS`
- `MAX_TOKENS_PER_RUN`
- `AUTONOMY`
- prompt wording
- routing rules
- tool implementations
- guardrails
- evaluation cases
- expected outcomes
- reference-data records
- trial counts
- grader/harness logic

The point of the final model comparison is to keep the system fixed while changing the live model.

## 9. Local cache clearing

Before the run, the notebook deletes:
- `__pycache__` directories
- `.pyc` files
- already-imported local project modules

The battery itself is started through a fresh Python subprocess, which gives the evaluation a new Python process.

`tools.py` also has a per-process data cache. A fresh subprocess means this cache starts empty.

This does **not** guarantee that an external model provider will disable its own prompt cache. Provider-side cached-token information, when available, remains part of the live provider response and can be stored in the result.

## 10. Free checks before the paid run

Before running the paid battery, the notebook checks:
- the package folders exist
- required scaffold files exist
- required Problem B data files exist
- the API key is loaded
- `BACKEND == "live"`
- `PROBLEM == "B"`
- the model is the assigned model
- prices match the entered prices
- v1/v2 is correct
- serial/parallel is correct
- the data path is correct
- the frozen evaluation set is exactly `REF-EV001` through `REF-EV040`
- there are 32 ordinary cases
- there are 8 negative cases
- the run therefore contains 56 trials

It also runs:

```bash
python3 run_eval.py --prompt
```

which is free and prints the exact model-facing prompt/configuration before the live battery.

## 11. Running D5

The paid command is:

```bash
python3 run_eval.py --battery
```

The notebook starts the same command through `subprocess.run()` so it can measure the wall-clock runtime.

A successful battery must finish normally and the summary must say:

```text
trials: 56
```

If the process crashes before completing the battery, do not use the incomplete run as the member's final model measurement.

## 12. Runtime measurement

The notebook records:

```text
Elapsed seconds
Elapsed minutes
```

using wall-clock time around the entire `run_eval.py --battery` process.

This is separate from the per-trial latency already recorded in the result JSON (`mean_seconds`, `median_seconds`). Different models/providers can take different amounts of time, so use the measured time from each teammate's own run.

## 13. Where the results are stored

The project itself writes the raw result to:

```text
A2_scaffold/results_d5_live.json
```

That file contains:
- the run configuration summary
- aggregate summary metrics
- all 56 trial records
- the judgement queue

The summary includes fields such as:

```text
trials
passed
pass_rate
negative_trials
negative_passed
negative_pass_rate
mean_turns
median_turns
worst_case_turns
tokens_in
tokens_out
cost_usd
mean_cost_usd
median_cost_usd
mean_seconds
median_seconds
```

Each trial record also contains its decision, evidence/tool use, token counts, cost data, timing, guardrail events, and pass/fail result.

## 14. Model-specific archive file

Because every run writes the same raw filename, teammates must not send only `results_d5_live.json` with no identification.

The notebook creates:

```text
<PACKAGE_ROOT>/D5_results/
```

and writes a second, model-specific JSON such as:

```text
d5_Ulfa_google_gemini-2.5-flash-lite_v2_parallel.json
```

This archived copy contains the complete original result plus a `runner_metadata` section with:

```json
{
  "member_name": "...",
  "model": "...",
  "price_in_usd_per_1m": 0.0,
  "price_out_usd_per_1m": 0.0,
  "version": "v2",
  "tool_call_mode": "parallel",
  "backend": "live",
  "problem": "B",
  "elapsed_seconds": 0.0,
  "elapsed_minutes": 0.0,
  "started_utc": "...",
  "finished_utc": "...",
  "raw_result_file": "A2_scaffold/results_d5_live.json",
  "code_sha256": {
    "...": "..."
  }
}
```

The SHA-256 values allow the team to verify that teammates ran the same project files.

**Each member should send the archived model-specific JSON back to the team.**

## 15. What to send back to the team

After a successful run, send:
1. the model-specific JSON from `D5_results/`;
2. the model name;
3. whether the run was v1 or v2;
4. the tool-call mode;
5. the input/output prices used and where they were verified;
6. any unusual provider error or interruption that occurred.

Do not rerun a complete 56-trial battery just because it contains a model failure. A genuine model failure is part of the experiment. Rerun only when the battery itself was invalid or incomplete, for example because the process crashed or the wrong configuration was used.

## 16. Final reminder for the team comparison

For the normal v2 model battery:
- same code
- same 40 cases
- same 56-trial schedule
- same v2 prompt/interface
- same parallel mode
- same routing rules and guardrails
- different assigned model
- matching price metadata for that model

For the one v1 pass:
- same evaluation battery
- same model as a v2 run
- v1 instead of v2

This keeps the comparisons interpretable.

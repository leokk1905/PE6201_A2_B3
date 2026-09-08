# D2(c) — Serial vs Parallel Tool-Invocation Experiment
## Problem B: Outpatient Referral Coordination

> **Status:** Experiment design and implementation steps are complete.  
> **Important:** The final full-set serial/parallel numbers must be populated from your own run. The executed scaffold supplies one valid parallel baseline for REF-5602, but it does not contain the required full serial-vs-parallel experiment.

---

# 1. Objective

D2(c) tests whether grouping independent tool calls into the same model turn reduces:
- tool-calling turns;
- repeated prompt/history tokens;
- cost;

without reducing correctness.

The experiment must compare the **same work** under:

```text
SERIAL
one tool call per model turn
```

versus:

```text
PARALLEL
multiple independent tool calls may be returned in one model turn
```

The dependency rule is:

> **Two calls may share a turn only when neither call requires the other's output.**

---

# 2. Problem B Dependency Graph

```text
get_referral
      |
      +-----------------------+
      |                       |
      v                       v
check_referral_criteria   lookup_patient
      |                       |
      +-----------+-----------+
                  |
                  v
           routing decision
                  |
        +---------+----------+
        |                    |
        v                    v
 request/escalate      get_clinic_slots
                             |
                             v
                         book_slot
```

## Rules

### Must be serial

`get_referral` is first and alone because downstream calls require fields from its observation.

`get_clinic_slots` must not run before the criteria result establishes:
- no red flag;
- correct department;
- mandatory tests present;
- urgency band/window.

`book_slot` must occur only after all booking preconditions and a legal slot are known.

### Safely parallel

```text
check_referral_criteria
+
lookup_patient
```

Both depend on `get_referral`, but neither needs the other's output.

### Conditional parallelism

Multiple `get_clinic_slots` queries can share a turn only if all queries are justified before seeing any of their results.

This is a trade-off:
- parallel queries can reduce a model turn;
- but a later query may be wasted if an earlier query already finds a slot.

---

# 3. REF-5602 Example

## Serial form

```text
Turn 1: get_referral
Turn 2: check_referral_criteria
Turn 3: lookup_patient
Turn 4: get_clinic_slots (near window)
Turn 5: get_clinic_slots (later window)
Turn 6: book_slot
Final: book
```

**6 tool calls, 6 tool-calling turns.**

## Parallel form used by the lecturer scaffold

```text
Turn 1:
  get_referral

Turn 2:
  check_referral_criteria
  lookup_patient

Turn 3:
  get_clinic_slots (near window)
  get_clinic_slots (later window)

Turn 4:
  book_slot

Final:
  book
```

**6 tool calls, 4 tool-calling turns.**

The final conclusion is not counted as a tool-calling turn.

---

# 4. Implementation Plan

Do not create two different agents.

Use the same:
- `agent.py`;
- tools;
- v2 descriptors;
- routing rules;
- guardrails;
- evaluation cases;
- model/backend.

Change only the grouping policy.

---

## Step 1 — Add a mode switch to `config.py`

Recommended:

```python
TOOL_CALL_MODE = os.environ.get("TOOL_CALL_MODE", "parallel")
# allowed: "serial" | "parallel"
```

Optional validation:

```python
if TOOL_CALL_MODE not in {"serial", "parallel"}:
    raise ValueError("TOOL_CALL_MODE must be 'serial' or 'parallel'")
```

Keep the submitted default that your team chooses, but both modes must be runnable for the D2(c) experiment.

---

## Step 2 — Make the scripted backend support both modes

The scaffold already stores multi-call steps such as:

```python
{
    "thought": "...",
    "calls": [
        ("check_referral_criteria", {...}),
        ("lookup_patient", {...})
    ]
}
```

Add a transformation that expands a batch into one call per move when `TOOL_CALL_MODE == "serial"`.

Example:

```python
def serialise_steps(steps):
    out = []

    for step in steps:
        calls = step.get("calls")

        if not calls or len(calls) <= 1:
            out.append(step)
            continue

        for i, call in enumerate(calls):
            out.append({
                "thought": (
                    step.get("thought", "")
                    if i == 0
                    else "Continue the serial execution of the independent calls."
                ),
                "calls": [call],
            })

    return out
```

Inside `ScriptedBackend.__init__`:

```python
steps = SCRIPTS[case_id]

if config.TOOL_CALL_MODE == "serial":
    steps = serialise_steps(steps)

self.steps = steps
```

### Caution

This transformation compares **the same planned calls regrouped into more turns**.

It does not model the possible serial advantage of seeing an early result and deciding to skip a later conditional call. Discuss that limitation in the analysis.

---

## Step 3 — Add serial/parallel instruction for the live backend

For live measurement, keep the same routing prompt but append a mode-specific tool-calling rule.

### Parallel

```text
When two or more required tool calls are independent,
return them together in the same `calls` list.
```

### Serial

```text
Return at most one tool call in each model move.
Wait for its observation before selecting another tool.
```

Do not change any business routing rule between modes.

---

## Step 4 — Capture actual API usage

The scaffold's scripted backend uses token **estimates**.

For final measured token/cost comparison, modify the live API wrapper to retain the API's usage object.

Conceptually:

```python
payload = json.load(r)

usage = payload.get("usage", {})
prompt_tokens = usage.get("prompt_tokens", 0)
completion_tokens = usage.get("completion_tokens", 0)
```

Store these values with each model move/run rather than estimating them manually.

The agent/harness should accumulate:
- `tokens_in`;
- `tokens_out`;
- `cost_usd`.

Do not call a scripted estimate a live measurement.

---

# 5. Experimental Controls

Before running the final comparison, freeze:

- D4 evaluation set;
- expected answer key;
- final v2 descriptors;
- prompt version;
- tool set;
- Poka-Yoke validations;
- autonomy setting;
- guardrail limits;
- model;
- temperature/settings;
- grader/checks.

The **only intended independent variable** is:

```text
TOOL_CALL_MODE
serial vs parallel
```

---

# 6. Evaluation Set

Run the **full final D4 evaluation set**.

Expected assignment shape:

```text
40 cases
8 negative cases
```

For D2(c), each configuration must receive the same cases.

If you use repeated trials, use the same trial counts in both configurations.

---

# 7. Per-Run Result Schema

Save one record per run, for example in:

```text
results/d2c_serial.jsonl
results/d2c_parallel.jsonl
```

Recommended fields:

```json
{
  "case_id": "REF-5602",
  "mode": "parallel",
  "decision": "book",
  "passed": true,
  "negative": false,
  "turns": 4,
  "tool_calls": 6,
  "tokens_in": 0,
  "tokens_out": 0,
  "cost_usd": 0.0,
  "seconds": 0.0
}
```

Use the actual values produced by the harness.

---

# 8. Batch Experiment Procedure

## Parallel run

```bash
TOOL_CALL_MODE=parallel python run_eval.py
```

Save/export the complete results as:

```text
results/d2c_parallel.jsonl
```

## Serial run

```bash
TOOL_CALL_MODE=serial python run_eval.py
```

Save/export as:

```text
results/d2c_serial.jsonl
```

If your environment does not support inline environment variables, set the variable in Python/Colab before importing/reloading `config`.

---

# 9. Metrics to Calculate

For each mode calculate:

```text
number of cases/trials
passing trials
overall pass rate
negative-case pass rate
mean turns
median turns
worst-case turns
total tool calls
mean tool calls
total input tokens
total output tokens
total cost
mean/median cost per case
mean/median latency
```

### Formulas

```python
pass_rate = passing_trials / total_trials

saving_pct = (
    serial_value - parallel_value
) / serial_value * 100
```

For a metric where a higher value is better (for example pass rate), report percentage-point change instead:

```python
pass_rate_change_pp = (
    parallel_pass_rate - serial_pass_rate
) * 100
```

---

# 10. Current Results Available From the Executed Scaffold

## REF-5602 — parallel scripted baseline

The executed Problem B notebook produced:

| Metric | Parallel scaffold result |
|---|---:|
| Decision | `book` |
| Code check | **PASS** |
| Tool-calling turns | **4** |
| Tool calls | **6** |
| Scripted estimated input tokens | 21,000 |
| Scripted estimated output tokens | 600 |
| Scripted estimated cost | US$0.00234 |
| Gate | `gate_passed` |
| Stopped by | `None` |

The trace was:

```text
Turn 1: get_referral
Turn 2: check_referral_criteria + lookup_patient
Turn 3: get_clinic_slots + get_clinic_slots
Turn 4: book_slot
Final: book
```

### Important limitation

The scaffold explicitly treats scripted token counts as **estimates**. Therefore:
- `4 turns` and `6 tool calls` are valid deterministic observations;
- `21,000 / 600 / $0.00234` are useful scaffold estimates;
- they are **not a substitute for final measured live token usage**.

---

# 11. Lecturer Worked Example — Context Only

The assignment's worked Problem B example states that REF-5602 can be grouped from:

```text
6 sequential turns
→
4 parallel turns
```

with an illustrative input-token estimate:

```text
13,200
→
8,400
```

or about **36% fewer input tokens** under the assumptions used in the brief.

Do **not** report those numbers as your team's experimental result. They are the lecturer's worked example and must be replaced by your own measurements.

---

# 12. Final Full-Set Results Table — Fill After Experiment

| Metric | Serial | Parallel | Change |
|---|---:|---:|---:|
| Cases/trials | `TBD` | same | — |
| Overall passing trials | `TBD` | `TBD` | `TBD` |
| Overall pass rate | `TBD` | `TBD` | `TBD pp` |
| Negative-case pass rate | `TBD` | `TBD` | `TBD pp` |
| Mean turns | `TBD` | `TBD` | `TBD %` |
| Median turns | `TBD` | `TBD` | `TBD %` |
| Worst legitimate turns | `TBD` | `TBD` | `TBD` |
| Total tool calls | `TBD` | `TBD` | `TBD %` |
| Total input tokens | `TBD` | `TBD` | `TBD %` |
| Total output tokens | `TBD` | `TBD` | `TBD %` |
| Total cost USD | `TBD` | `TBD` | `TBD %` |
| Mean latency | `TBD` | `TBD` | `TBD %` |

---

# 13. Correctness Analysis

Parallelisation is acceptable only if correctness does not materially worsen.

### If pass rates are equal

Use wording such as:

> Parallel grouping reduced the median tool-calling turn count from `[x]` to `[y]` (`[z%]`) and input tokens from `[x]` to `[y]` (`[z%]`) while pass rate remained `[p%]`. The result supports grouping calls that are independent and required regardless of one another's outputs.

### If parallel pass rate falls

Do not hide it. Investigate cases where:
- the model would have benefited from seeing an intermediate observation;
- parallel execution caused a conditionally unnecessary call;
- the model selected later actions too early.

Possible conclusion:

> Parallelism reduced turns but removed an intermediate decision point. We therefore narrowed the parallel boundary rather than maximising the number of calls per turn.

---

# 14. Slot-Query Trade-Off Analysis

REF-5602 contains a useful design trade-off.

Parallel version:

```text
get_clinic_slots(near window)
+
get_clinic_slots(later window)
```

Benefit:
- one fewer model turn.

Risk:
- if the near query already finds an acceptable slot, the later query was unnecessary.

Therefore compare two possible final policies:

### Policy A — aggressive

Parallelise:
- criteria + patient;
- both slot-window queries.

### Policy B — conservative

Parallelise:
- criteria + patient only.

Keep conditional slot queries serial.

Recommended decision rule:

> **Parallelise calls that are independent and known to be required before either observation is seen. Keep conditionally necessary calls serial unless measured evidence shows a clear net benefit without correctness loss.**

---

# 15. Recommended Final Result Interpretation

Fill from measured results:

> Across `[N]` cases / `[T]` trials, serial execution achieved `[x%]` pass rate and parallel execution achieved `[y%]`. Parallel grouping changed median turns from `[a]` to `[b]`, input tokens from `[c]` to `[d]`, and total cost from `$[e]` to `$[f]`. The largest savings came from grouping `check_referral_criteria` with `lookup_patient`, which are independent after `get_referral`. `[Slot queries were/weren't]` retained in the same turn because `[measured reason]`. We therefore adopted `[final policy]` as the dependency rule for the final system.

---

# 16. D2(c) Completion Checklist

- [ ] Serial mode implemented
- [ ] Parallel mode implemented
- [ ] Same agent used in both modes
- [ ] Same v2 tool descriptors used
- [ ] Same prompt/routing rules used
- [ ] Same evaluation set/labels used
- [ ] Same model/settings used for measured comparison
- [ ] Actual API usage captured for live token measurement
- [ ] Per-run outputs saved
- [ ] Turns compared
- [ ] Tool-call counts compared
- [ ] Input/output tokens compared
- [ ] Cost compared
- [ ] Overall correctness compared
- [ ] Negative-case correctness compared
- [ ] Conditional-call trade-off discussed
- [ ] Final dependency/parallelisation policy stated
- [ ] Results summarised in Report Section 2

# D7 — two failures, each a duplicated agent minus one line

Source: the working agent in `D5/D5_live_model_runner/A2_scaffold/` +
`A2_reference_data/` (D5's own copy is left untouched - see below).
Backend: **scripted** everywhere in D7. No API key, no network calls.

```
D7/
  failure1_step_cap_loop/     duplicate of the working agent, plus:
    A2_scaffold/agent_broken.py   agent.py minus the step cap (2 lines, see its own header)
    A2_scaffold/run_failure1.py   python run_failure1.py

  failure2_interface_band/    duplicate of the working agent, no extra broken file:
    A2_scaffold/run_failure2.py   python run_failure2.py
```

Every other file in each `A2_scaffold/` is an unmodified copy of D5's
agent - diff them to confirm. The only edit made to any copy is
`config.py`: `BACKEND` is forced to `"scripted"` (D5's own copy is
mid-use for the live model battery and stays on `"live"` - untouched).
`python run_eval.py` and `python run_eval.py --battery` (the frozen
40-case / 56-trial set, `REF-EV001`..`040`) both still run clean in
both folders, against the real, unbroken agent - that's what each
`run_failureN.py` uses as its baseline and its regression check.

- **Failure 1 (loop):** `agent_broken.py` deletes the step cap (both
  the guardrail call and the loop's own hard backstop). `run_failure1.py`
  measures the real turn distribution across the full 40-case battery
  (median 4.0, worst-case 4), traps the broken agent in a non-repeating
  re-query loop, shows what actually stops it (the budget ceiling - much
  later and more expensively than a step cap would), then restores the
  cap at (worst-case + 1 = 5) and shows a loud `step_cap` stop with zero
  regression across all 40 cases.

- **Failure 2 (interface):** no new file needed - `tools.py` already
  ships a v1/v2 experiment for `get_clinic_slots` (`config.VERSION`):
  v1 doesn't accept or return `band` at all; v2 requires it on input
  and includes it on every returned row. `run_failure2.py` sets
  `VERSION="v1"` (the interface deletion, already in the codebase),
  traps it with a real urgent referral (`REF-EV003`) whose careless,
  band-blind slot query returns a routine slot 35 days later than the
  real urgent one, and the agent books it - a confidently wrong answer
  the code check alone would pass. Setting `VERSION="v2"` back (the
  fix, and the scaffold's own documented default) makes the identical
  call impossible to construct: Python rejects it with `TypeError`
  before any tool runs, no if/else added.

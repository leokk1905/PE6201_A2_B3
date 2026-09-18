# D7 — two failures, each a duplicated agent minus one line

Source: the working agent in `D5/D5_live_model_runner/A2_scaffold/` +
`A2_reference_data/` (D5's own copy is left untouched - see below).
Backend: **scripted** everywhere in D7. No API key, no network calls.

```
D7/
  failure1_step_cap_loop/     duplicate of the working agent, plus:
    A2_scaffold/agent_broken.py   agent.py minus the step cap (2 lines, see its own header)
    A2_scaffold/run_failure1.py   python run_failure1.py

  failure2_interface_band/    duplicate of the working agent, plus:
    A2_scaffold/tools_broken.py   tools.py minus `band` being required (1 word, see its own header)
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

Both `run_failureN.py` scripts call the real `harness.code_check()` on
the trap's output and print an actual `PASS`/`FAIL` verdict against
the case's real answer-key entry (not just a description of the
record) - each script asserts the broken run genuinely fails that
check, so "the agent is wrong" is a verified fact, not narration.

- **Failure 1 (loop):** `agent_broken.py` deletes the step cap (both
  the guardrail call and the loop's own hard backstop). `run_failure1.py`
  measures the real turn distribution across the full 40-case battery
  (median 4.0, worst-case 4), traps the broken agent in a non-repeating
  re-query loop, shows what actually stops it (the budget ceiling - much
  later and more expensively than a step cap would, and it fails
  `REF-5602`'s own code check: `decision 'escalate', expected 'book'`),
  then restores the cap at (worst-case + 1 = 5) and shows a loud
  `step_cap` stop with zero regression across all 40 cases.

- **Failure 2 (interface):** `tools_broken.py` makes `band` optional on
  `_get_clinic_slots_v2` - the FINAL interface this agent ships with,
  not the separate `_get_clinic_slots_v1` that already exists in
  `tools.py` for the unrelated D2(b) live-model comparison (swapping to
  that would be choosing between two things that already exist, not a
  deletion). `run_failure2.py` traps it with a real urgent referral
  (`REF-EV003`) whose band-blind slot query returns a routine slot 35
  days later than the real urgent one; the agent books it, and the code
  check confirms this genuinely **fails** (`booked.clinic 'CARD-C2',
  expected 'CARD-C1'`, etc.) even though the top-level decision alone
  would look like a pass. Restoring `tools.py` (band required again)
  makes the identical call impossible to construct: Python rejects it
  with `TypeError` before any tool runs, no if/else added.

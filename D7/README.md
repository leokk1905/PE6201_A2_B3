# D7 — two failures, each a duplicated agent minus one line

Backend: **scripted** everywhere below. No API key, no network calls.

```
D7/
  failure1_step_cap_loop/     duplicate of the working agent, plus:
    A2_scaffold/agent_broken.py   agent.py minus the step cap (2 lines, see its own header)
    A2_scaffold/run_failure1.py   python run_failure1.py

  failure2_interface_band/    duplicate of the working agent, plus:
    A2_scaffold/tools_broken.py   tools.py minus `band` being required (1 line, see its own header)
    A2_scaffold/run_failure2.py   python run_failure2.py
```

Every other file in each `A2_scaffold/` is an unmodified copy of the
agent in `our_works/A2_scaffold/A2_scaffold/` - diff them to confirm.
`python run_eval.py` still runs clean in both folders, against the
real, unbroken agent, which is how each `run_failureN.py` proves its
fix by comparison.

- **Failure 1 (loop):** `agent_broken.py` deletes the step cap.
  `run_failure1.py` measures a real turn distribution across 6
  answer-key-verified cases, traps the broken agent in a non-repeating
  re-query loop, shows what actually stops it, then restores the cap
  at (worst-case + 1) and shows a loud `step_cap` stop with no
  regression on the 6 cases.
- **Failure 2 (interface):** `tools_broken.py` makes `get_clinic_slots`'s
  `band` argument optional. `run_failure2.py` traps it with a real
  urgent referral whose call omits `band`, showing a confidently wrong
  booking that the code check alone would pass, then restores the
  required argument - the call is rejected by Python itself, no
  if/else added.

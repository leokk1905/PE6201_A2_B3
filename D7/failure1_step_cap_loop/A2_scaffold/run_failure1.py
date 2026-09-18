#!/usr/bin/env python3
"""
PE6201 · A2 · D7 FAILURE 1 — the loop
====================================================================
    python3 run_failure1.py

Backend: scripted. Zero API key, zero network calls, deterministic.

WHAT WAS DELETED
    agent_broken.py is agent.py with two lines commented out - the
    loop's own hard turn-backstop and guards.check_turns(turns), the
    step cap (guardrails.py mechanism #1). Diff the two files to see
    the whole change. THE FIX is simply using agent.py (unmodified)
    instead of agent_broken.py - nothing else changes.

WHAT THIS SCRIPT DOES, IN ORDER
    1. Runs six real, answer-key-verified Problem B cases through the
       WORKING agent (agent.py) to measure the turn distribution.
    2. Builds a trap case designed to confuse the loop without ever
       repeating an identical tool call (so de-duplication, a
       DIFFERENT guardrail, does not mask this specific failure).
    3. Runs the trap through agent_broken.run_case() - the step cap
       is gone - and shows what actually stops it.
    4. Runs the SAME trap through agent.run_case() (the restored
       agent) with a cap set to worst-case-legitimate + 1, and checks
       it stops LOUDLY with reason "step_cap".
    5. Re-runs the six baseline cases with that cap enforced, to prove
       the fix does not truncate any legitimate run.
====================================================================
"""
import config
import backends
from guardrails import GuardrailStop

BASELINE_CASES = ["REF-5602", "REF-5750", "REF-5764", "REF-5766", "REF-5590", "REF-5772"]
TRAP_CASE = "REF-5602"                 # real, valid referral - only its SCRIPT changes
KILL_SWITCH_TURNS = 60                  # Step 2's "hard kill-switch" - bounds the
                                         # OFF-demo so it cannot hang a marker's
                                         # machine. It is not the fix.


def run_baseline(run_case_fn):
    return [run_case_fn(cid, problem="B") for cid in BASELINE_CASES]


def turn_stats(records):
    turns = [r["turns"] for r in records]
    import statistics
    return statistics.median(turns), max(turns), turns


def looping_trap_script():
    """Turns 1-2 are REF-5602's real opening (fetch the referral, then
    criteria+patient together) - the run looks completely normal up to
    here. From turn 3 it never converges: it re-queries get_clinic_slots
    with the window pushed one more day out each time - a DIFFERENT
    call every time, so duplicate-action detection (untouched, still
    active) never fires. Only the step cap could ever end this."""
    real = backends.SCRIPTS["REF-5602"]
    steps = list(real[:2])
    for i in range(KILL_SWITCH_TURNS - len(steps)):
        to_date = "2026-%02d-%02d" % (9 + i // 28, 1 + i % 28)
        steps.append({
            "thought": "Still nothing books cleanly - widen the window a "
                      "little further, to %s." % to_date,
            "calls": [("get_clinic_slots", {"specialty": "OPH", "band": "routine",
                                            "from": "2026-09-09", "to": to_date})],
        })
    return steps


def main():
    print()
    print(config.summary())

    from agent import run_case as run_case_fixed
    print()
    print("=" * 68)
    print("  BASELINE (Phase 2 Step 1) - working agent, %d real cases"
          % len(BASELINE_CASES))
    print("=" * 68)
    baseline = run_baseline(run_case_fixed)
    median, worst, turns = turn_stats(baseline)
    cap = worst + 1
    print("  turns per case: %s" % turns)
    print("  median turns = %s   worst-case turns = %s   ->  data-driven cap = %d"
          % (median, worst, cap))

    original_trap_script = backends.SCRIPTS[TRAP_CASE]
    backends.SCRIPTS[TRAP_CASE] = looping_trap_script()

    print()
    print("=" * 68)
    print("  FIX OFF - agent_broken.run_case() (step cap deleted)")
    print("=" * 68)
    from agent_broken import run_case as run_case_broken
    off = run_case_broken(TRAP_CASE, problem="B")
    print("  turns %d · tool calls %d · tokens %d · cost US$%.5f"
          % (off["turns"], len(off["evidence"]),
             off["tokens_in"] + off["tokens_out"], off["cost_usd"]))
    print("  decision: %r    stopped_by: %r" % (off["decision"], off["stopped_by"]))
    print("  guardrails fired: %s"
          % ([g["guardrail"] for g in off["guardrails_fired"]] or "NONE"))
    if off["stopped_by"] is None:
        print("  Nothing stopped it before this script's own %d-turn kill-switch -"
              % KILL_SWITCH_TURNS)
        print("  left alone this keeps going until a real bill or a real OOM ends it.")
    else:
        print("  The step cap is gone, but %r still caught it - later, and after"
              % off["stopped_by"])
        print("  burning far more than a tight step cap would ever have allowed.")

    print()
    print("=" * 68)
    print("  FIX ON - agent.run_case() (unmodified), cap = %d (data-driven)" % cap)
    print("=" * 68)
    config.MAX_TURNS = cap
    on = run_case_fixed(TRAP_CASE, problem="B")
    config.MAX_TURNS = 8   # restore the shipped production value
    print("  turns %d · tool calls %d · tokens %d · cost US$%.5f"
          % (on["turns"], len(on["evidence"]),
             on["tokens_in"] + on["tokens_out"], on["cost_usd"]))
    print("  decision: %r    stopped_by: %r" % (on["decision"], on["stopped_by"]))
    assert on["stopped_by"] == "step_cap", (
        "expected the restored agent to raise step_cap loudly; got %r" % on["stopped_by"])
    print("  PASS - stopped LOUDLY with reason %r, not a silent empty answer."
          % on["stopped_by"])

    backends.SCRIPTS[TRAP_CASE] = original_trap_script   # undo the trap

    print()
    print("=" * 68)
    print("  REGRESSION - the cap must not truncate legitimate runs")
    print("=" * 68)
    config.MAX_TURNS = cap
    regressed = run_baseline(run_case_fixed)
    config.MAX_TURNS = 8
    truncated = [r for r in regressed if r["stopped_by"] == "step_cap"]
    print("  %d of %d legitimate cases hit the new cap of %d"
          % (len(truncated), len(regressed), cap))
    print("  %s - worst legitimate run measured %d turns, cap is %d."
          % ("PASS" if not truncated else "FAIL", worst, cap))

    print()
    print("=" * 68)
    print("  WHY THE CODE LAYER, AND WHY NOT THE OTHER TWO")
    print("=" * 68)
    print("  De-duplication was left untouched and could not have caught this:")
    print("  every get_clinic_slots call in the trap uses a different window,")
    print("  so no (tool, args) signature ever repeats.")
    print("  A prompt instruction cannot be relied on either: the scripted")
    print("  backend never reads the prompt at all (see prompt.py), so a")
    print("  prompt fix would have had EXACTLY ZERO effect on this run.")
    print("  Only a check inside the loop itself ends a run that keeps making")
    print("  progress-shaped calls without making progress.")
    print()


if __name__ == "__main__":
    main()

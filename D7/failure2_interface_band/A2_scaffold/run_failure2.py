#!/usr/bin/env python3
"""
PE6201 · A2 · D7 FAILURE 2 — the interface
====================================================================
    python3 run_failure2.py

Backend: scripted. Zero API key, zero network calls, deterministic.

WHY THE INTERFACE, NOT THE PROMPT
    prompt.py says outright: "On the scripted backend [the prompt] is
    ignored - the moves are pre-written, so no prompt is ever sent."
    D7 requires zero live calls, so a prompt deletion would have
    LITERALLY ZERO EFFECT to demonstrate here. The interface is the
    one non-guardrail layer that DOES still execute for real on this
    backend, because tools.call() genuinely dispatches to the real
    tool function no matter which backend chose to call it.

WHAT WAS DELETED
    tools_broken.py is tools.py with one word changed - see the
    header of that file. `band` is optional there; `band` is required
    in tools.py. THE FIX is simply using tools.py (unmodified) instead
    of tools_broken.py - nothing else changes, and no if/else is added
    anywhere to catch the missing argument.

THE TRAP
    REF-5631 (backends.py) - a real, answer-keyed CARD referral whose
    correct band is URGENT. Its scripted move list omits `band` from
    the get_clinic_slots call entirely - exactly the omission the
    deleted parameter exists to make impossible.
====================================================================
"""
import agent
import backends
import config
import tools
import tools_broken
from agent import run_case

TRAP_CASE = "REF-5631"

# The trap: a real, answer-keyed CARD referral whose correct band is
# URGENT (2-week window; the answer key expects CARD-C1 on 2026-09-16).
# Turns 1-2 are the real, correct opening. Turn 3 is the mistake:
# `band` is missing from the call entirely - exactly the omission the
# deleted parameter in tools_broken.py exists to make impossible. Kept
# out of backends.py's shared SCRIPTS dict so `python run_eval.py`
# still runs clean against the unmodified interface (see backends.py).
TRAP_SCRIPT = [
    {"thought": "Turn 1 must run alone.",
     "calls": [("get_referral", {"referral_id": TRAP_CASE})]},
    {"thought": "Criteria and patient depend on nothing but the referral.",
     "calls": [("check_referral_criteria", {"specialty": "CARD", "referral_id": TRAP_CASE}),
               ("lookup_patient", {"patient_id": "P-1233"})]},
    {"thought": "Query the window for a slot.",   # <- band never mentioned
     "calls": [("get_clinic_slots",
                {"specialty": "CARD", "from": "2026-09-09", "to": "2026-11-04"})]},
    {"thought": "A slot exists - book it.",
     "calls": [("book_slot", {"clinic": "CARD-C10", "date": "2026-10-07",
                              "time": "09:00", "referral_id": TRAP_CASE})]},
    {"final": {"decision": "book",
              "booked": {"clinic": "CARD-C10", "date": "2026-10-07", "time": "09:00"},
              "reason": "Slot found and booked."},
     "thought": "done"},
]


def main():
    print()
    print(config.summary())

    backends.SCRIPTS[TRAP_CASE] = TRAP_SCRIPT

    correct = tools.get_clinic_slots("CARD", "urgent", **{"from": "2026-09-09", "to": "2026-11-04"})
    correct_best = sorted(correct, key=lambda s: (s["date"], s["time"]))[0]
    print()
    print("  the RIGHT answer for %s (urgent CARD, 2-week window): %s on %s at %s"
          % (TRAP_CASE, correct_best["clinic"], correct_best["date"], correct_best["time"]))

    print()
    print("=" * 68)
    print("  FIX OFF - agent.tools swapped for tools_broken (band optional)")
    print("=" * 68)
    agent.tools = tools_broken           # the ONLY thing this demo changes
    off = run_case(TRAP_CASE, problem="B")
    agent.tools = tools                  # restore immediately after
    print("  turns %d · tool calls %d · tokens %d · cost US$%.5f"
          % (off["turns"], len(off["evidence"]),
             off["tokens_in"] + off["tokens_out"], off["cost_usd"]))
    print("  decision: %r    booked: %s" % (off["decision"], off.get("booked")))
    days_late = _days_between(correct_best["date"], off["booked"]["date"])
    print("  code_check would PASS this: decision=='book' matches the answer key.")
    print("  It is wrong anyway - a 2-week-urgent cardiac referral was silently")
    print("  booked %d days later than the slot that actually existed for it."
          % days_late)

    print()
    print("=" * 68)
    print("  FIX ON - agent.tools is tools.py, unmodified (band required)")
    print("=" * 68)
    try:
        run_case(TRAP_CASE, problem="B")
        raise AssertionError("expected the restored interface to reject the "
                             "band-less call; it did not")
    except TypeError as exc:
        print("  REJECTED before any tool body ran: %s" % exc)
        print("  PASS - the interface makes the wrong call impossible to construct.")
        print("  No if/else was added anywhere to detect a missing band; Python's")
        print("  own call-signature check did the work.")

    print()
    print("=" * 68)
    print("  REGRESSION - the restored signature must not break real callers")
    print("=" * 68)
    ok = run_case("REF-5602", problem="B")
    print("  REF-5602 (unrelated, real case) still decides %r in %d turns - "
          "every real script"
          % (ok["decision"], ok["turns"]))
    print("  already names `band` explicitly, so only a call that never should")
    print("  have been made in the first place is affected.")

    print()
    print("=" * 68)
    print("  WHY THE INTERFACE LAYER, AND WHY NOT THE OTHER TWO")
    print("=" * 68)
    print("  A code-layer guard (step cap, budget, de-duplication) only ever")
    print("  watches turns and repeats - nothing about this run loops or")
    print("  overspends, so none of Failure 1's guards would ever see it.")
    print("  A prompt instruction ('always pass band') is not read by the")
    print("  scripted backend at all, and even live it is only advice - nothing")
    print("  stops a model from omitting the argument anyway. Only the")
    print("  function's own signature makes the mistake impossible to type.")
    print()

    del backends.SCRIPTS[TRAP_CASE]   # tidy up: not part of the shared battery


def _days_between(a, b):
    from datetime import date
    ay, am, ad = (int(x) for x in a.split("-"))
    by, bm, bd = (int(x) for x in b.split("-"))
    return (date(by, bm, bd) - date(ay, am, ad)).days


if __name__ == "__main__":
    main()

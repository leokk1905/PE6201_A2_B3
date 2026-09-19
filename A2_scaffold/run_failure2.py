#!/usr/bin/env python3
"""
PE6201 · A2 · D7 FAILURE 2 — the interface
====================================================================
    python3 run_failure2.py

Backend: scripted. Zero API key, zero network calls, deterministic.

WHY THE INTERFACE, NOT THE PROMPT
    prompt.py says outright that on the scripted backend the prompt is
    ignored - the moves are pre-written, so no prompt is ever sent.
    D7 requires zero live calls, so a prompt deletion would have
    LITERALLY ZERO EFFECT to demonstrate here. The interface is the
    one non-guardrail layer that DOES still execute for real on this
    backend, because tools.call() genuinely dispatches to the real
    tool function no matter which backend chose to call it.

WHAT WAS DELETED
    tools_broken.py is tools.py with one word changed - see its own
    header. `_get_clinic_slots_v2` - the FINAL interface this agent
    submits with - has `band` made optional there. THE FIX is simply
    using tools.py (unmodified) instead of tools_broken.py - nothing
    else changes, and no if/else is added anywhere to catch the
    missing argument. (tools.py separately ships a `_get_clinic_slots_v1`
    for the unrelated D2(b) live-model comparison; swapping to THAT is
    choosing between two things that already exist, not a deletion,
    which is why this failure uses its own broken copy instead.)

THE TRAP
    REF-EV003 (backends.py) - a real, answer-keyed CARD referral from
    the 40-case battery whose correct band is URGENT (2-week window;
    the answer key expects CARD-C1 on 2026-09-16). Its scripted move
    list omits `band` from the get_clinic_slots call entirely - the
    omission the deleted parameter exists to make impossible - and
    picks CARD-C2, a real routine-band slot 35 days later.
====================================================================
"""
import agent
import backends
import config
import tools
import tools_broken
from harness import code_check, load_key

TRAP_CASE = "REF-EV003"

TRAP_SCRIPT = [
    {"thought": "Turn 1 must run alone.",
     "calls": [("get_referral", {"referral_id": TRAP_CASE})]},
    {"thought": "Criteria and patient depend on nothing but the referral.",
     "calls": [("check_referral_criteria", {"specialty": "CARD", "referral_id": TRAP_CASE}),
               ("lookup_patient", {"patient_id": "P-EV003"})]},
    {"thought": "Query for a slot - the interface does not require a band, "
               "so none is given.",
     "calls": [("get_clinic_slots",
                {"specialty": "CARD", "from": "2026-09-09", "to": "2026-11-04"})]},
    {"thought": "CARD-C2 has the most capacity remaining of the slots "
               "returned - book it.",
     "calls": [("book_slot", {"clinic": "CARD-C2", "date": "2026-10-21",
                              "time": "10:00", "referral_id": TRAP_CASE})]},
    {"final": {"decision": "book",
              "booked": {"clinic": "CARD-C2", "date": "2026-10-21", "time": "10:00"},
              "reason": "Slot found and booked."},
     "thought": "done"},
]


def run_trap(broken):
    original = backends.SCRIPTS.get(TRAP_CASE)
    backends.SCRIPTS[TRAP_CASE] = TRAP_SCRIPT
    agent.tools = tools_broken if broken else tools   # the ONLY thing this demo changes
    try:
        return agent.run_case(TRAP_CASE, problem="B")
    finally:
        agent.tools = tools                            # always leave it restored
        if original is None:
            del backends.SCRIPTS[TRAP_CASE]
        else:
            backends.SCRIPTS[TRAP_CASE] = original


def main():
    print()
    print(config.summary())

    key = load_key("B")
    expected = key[TRAP_CASE]
    correct = expected["booked"]
    print()
    print("  the RIGHT answer for %s (urgent CARD, 2-week window): %s on %s at %s"
          % (TRAP_CASE, correct["clinic"], correct["date"], correct["time"]))

    print()
    print("=" * 68)
    print("  FIX OFF - tools_broken.py (band optional on _get_clinic_slots_v2)")
    print("=" * 68)
    off = run_trap(broken=True)
    ok, fails = code_check(off, expected)
    print("  turns %d · tool calls %d · tokens %d · cost US$%.5f"
          % (off["turns"], len(off["evidence"]),
             off["tokens_in"] + off["tokens_out"], off["cost_usd"]))
    print("  decision: %r    booked: %s" % (off["decision"], off.get("booked")))
    print("  CODE CHECK: %s" % ("PASS" if ok else "FAIL"))
    for f in fails:
        print("      %s" % f)
    days_late = _days_between(correct["date"], off["booked"]["date"])
    print("  The DECISION alone ('book') matches the answer key - a pass-rate")
    print("  table that only compared decisions would call this a pass. The")
    print("  full code check (which also checks the booked slot) correctly")
    print("  fails it: a 2-week-urgent referral was silently booked %d days"
          % days_late)
    print("  later than the slot that actually existed for it.")
    assert not ok, "expected the broken interface to fail the code check"

    print()
    print("=" * 68)
    print("  FIX ON - tools.py, unmodified (band required)")
    print("=" * 68)
    try:
        run_trap(broken=False)
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
    ok_case = agent.run_case("REF-5602", problem="B")
    ok2, fails2 = code_check(ok_case, load_key("B")["REF-5602"])
    print("  REF-5602 (unrelated, real case): CODE CHECK %s"
          % ("PASS" if ok2 else "FAIL"))
    print("  every real script already names `band` explicitly, so only a call")
    print("  that never should have been made in the first place is affected.")

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


def _days_between(a, b):
    from datetime import date
    ay, am, ad = (int(x) for x in a.split("-"))
    by, bm, bd = (int(x) for x in b.split("-"))
    return (date(by, bm, bd) - date(ay, am, ad)).days


if __name__ == "__main__":
    main()

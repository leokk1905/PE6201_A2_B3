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

WHAT WAS DELETED - NOTHING NEW WRITTEN, ONLY A SWITCH FLIPPED
    tools.py already ships this failure as a controlled experiment for
    D2(b): get_clinic_slots has a v1 interface (band not accepted, not
    required, NOT EVEN RETURNED in the observation) and a v2 interface
    (band required on input AND present on every returned row). Which
    one answers to the name `get_clinic_slots` is chosen once, at
    import time, by config.VERSION:

        get_clinic_slots = (_get_clinic_slots_v1
                            if config.VERSION == "v1"
                            else _get_clinic_slots_v2)

    No new "broken" file exists for this failure - v1 already IS the
    working agent minus the interface constraint. THE FIX is setting
    config.VERSION back to "v2" (the documented default) before the
    module is (re)imported - exactly what the scaffold's own comment
    in config.py already says to do ("restart the runtime when you
    switch versions"). This script does that with importlib.reload()
    instead of a second process, so both runs live in one log.

THE TRAP
    REF-EV003 - a real, answer-keyed CARD referral from the 40-case
    battery whose correct band is URGENT (2-week window; the answer
    key expects CARD-C1 on 2026-09-16). Under v1, `get_clinic_slots`
    does not require or return `band` at all, so a wider, careless
    window query returns urgent AND routine slots looking identical -
    nothing in the tool's own output tells the agent which is which.
    The scripted "confused" move picks CARD-C2 on 2026-10-21, a real
    slot from that same undifferentiated list, 35 days later than the
    urgent slot that actually existed.
====================================================================
"""
import importlib

import backends
import config

TRAP_CASE = "REF-EV003"
CORRECT = {"clinic": "CARD-C1", "date": "2026-09-16", "time": "08:30"}

TRAP_SCRIPT = [
    {"thought": "Turn 1 must run alone.",
     "calls": [("get_referral", {"referral_id": TRAP_CASE})]},
    {"thought": "Criteria and patient depend on nothing but the referral.",
     "calls": [("check_referral_criteria", {"specialty": "CARD", "referral_id": TRAP_CASE}),
               ("lookup_patient", {"patient_id": "P-EV003"})]},
    {"thought": "Query for a slot - the interface does not ask for a band, "
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


def run_with_version(version, case_id=TRAP_CASE):
    config.VERSION = version
    import tools
    importlib.reload(tools)          # re-runs the v1/v2 binding at the top of tools.py
    import agent
    importlib.reload(agent)          # agent.py's `import tools` now sees the reload

    if case_id != TRAP_CASE:
        return agent.run_case(case_id, problem="B")

    original = backends.SCRIPTS.get(TRAP_CASE)
    backends.SCRIPTS[TRAP_CASE] = TRAP_SCRIPT
    try:
        return agent.run_case(TRAP_CASE, problem="B")
    finally:
        if original is None:
            del backends.SCRIPTS[TRAP_CASE]
        else:
            backends.SCRIPTS[TRAP_CASE] = original


def main():
    print()
    print(config.summary())
    print()
    print("  the RIGHT answer for %s (urgent CARD, 2-week window): %s on %s at %s"
          % (TRAP_CASE, CORRECT["clinic"], CORRECT["date"], CORRECT["time"]))

    print()
    print("=" * 68)
    print("  FIX OFF - config.VERSION = 'v1' (band not accepted or returned)")
    print("=" * 68)
    off = run_with_version("v1")
    print("  turns %d · tool calls %d · tokens %d · cost US$%.5f"
          % (off["turns"], len(off["evidence"]),
             off["tokens_in"] + off["tokens_out"], off["cost_usd"]))
    print("  decision: %r    booked: %s" % (off["decision"], off.get("booked")))
    days_late = _days_between(CORRECT["date"], off["booked"]["date"])
    print("  code_check would PASS this: decision=='book' matches the answer key.")
    print("  It is wrong anyway - a 2-week-urgent cardiac referral was silently")
    print("  booked %d days later than the slot that actually existed for it."
          % days_late)

    print()
    print("=" * 68)
    print("  FIX ON - config.VERSION = 'v2' (band required on input and output)")
    print("=" * 68)
    try:
        on = run_with_version("v2")
        raise AssertionError("expected the v2 interface to reject the "
                             "band-less call; it did not")
    except TypeError as exc:
        print("  REJECTED before any tool body ran: %s" % exc)
        print("  PASS - v2's get_clinic_slots does not accept a call missing")
        print("  `band` at all; the same trap script cannot even execute under")
        print("  the restored interface. No if/else was added anywhere to")
        print("  detect this - Python's own call-signature check did the work.")

    print()
    print("=" * 68)
    print("  REGRESSION - v2 must not break real callers")
    print("=" * 68)
    check = run_with_version("v2", case_id="REF-5602")
    print("  REF-5602 (unrelated, real case) still decides %r in %d turns"
          % (check["decision"], check["turns"]))

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
    print("  function's own signature - and, here, its own RETURN SHAPE - can")
    print("  make the missing distinction impossible to ignore.")
    print()


def _days_between(a, b):
    from datetime import date
    ay, am, ad = (int(x) for x in a.split("-"))
    by, bm, bd = (int(x) for x in b.split("-"))
    return (date(by, bm, bd) - date(ay, am, ad)).days


if __name__ == "__main__":
    main()

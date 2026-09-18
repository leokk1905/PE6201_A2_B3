"""
PE6201 · A2 scaffold — THE TWO BACKENDS
====================================================================
A backend answers ONE question: given the conversation so far, what
does the agent do next?

It returns either
    {"tool": "name", "args": {...}, "thought": "..."}      -> call a tool
    {"final": {...}, "thought": "..."}                     -> conclude

EXACTLY ONE FUNCTION IN THIS WHOLE REPOSITORY KNOWS A VENDOR EXISTS.
It is `_live_call` at the bottom. That is the D5 requirement, and it is
what makes swapping models a one-string change.

--------------------------------------------------------------------
WHY THE SCRIPTED BACKEND IS NOT A TOY

It replays a fixed sequence of decisions for a known case. That makes
your whole run deterministic, free, and reproducible by a stranger -
which is what D5(a) is marked on, and what makes D3(b) and D7 cost
nothing.

It is also the honest way to test your CODE. A guardrail either fires
or it does not; a model has no say in that. Scripting the model's
moves is how you test the parts you wrote.
====================================================================
"""
import json
import urllib.request

import config


# =====================================================================
# SCRIPTED
# =====================================================================
# One entry per case you have scripted. The value is the list of moves
# the "model" makes, in order.
#
# ADD YOUR OWN CASES HERE. To script a case: work out what a correct
# agent would do, step by step, and write the steps down. If you cannot
# write them down, you do not yet understand the case - which is
# useful to discover now rather than at 2am on the 13th.
SCRIPTS = {

    # ---------------------------------------------------------------
    # PROBLEM B · REF-5602 - the booking from Appendix A.
    # Six tool calls. Turns 2 and 3 each fire two calls at once, so the
    # run is FOUR turns rather than six. See D2(c) in the brief.
    # ---------------------------------------------------------------
    "REF-5602": [
        {"thought": "I have a referral id and nothing else. Fetch the record.",
         "calls": [("get_referral", {"referral_id": "REF-5602"})]},

        {"thought": "Two things I need next do not depend on each other: "
                    "the specialty's rules, and whether this patient already "
                    "has an appointment. Fire both together.",
         "calls": [("check_referral_criteria", {"specialty": "OPH",
                                                "referral_id": "REF-5602"}),
                   ("lookup_patient", {"patient_id": "P-1180"})]},

        {"thought": "No red flag, right department, VF-01 attached, no "
                    "duplicate. Band is routine, so the window runs 8 weeks "
                    "from as_of 2026-09-09, to 2026-11-04. I will query both "
                    "halves of that window at once. This is a gamble: if the "
                    "near half had a slot, the second query was wasted.",
         "calls": [("get_clinic_slots", {"specialty": "OPH", "band": "routine",
                                         "from": "2026-09-09", "to": "2026-09-30"}),
                   ("get_clinic_slots", {"specialty": "OPH", "band": "routine",
                                         "from": "2026-10-01", "to": "2026-11-04"})]},

        {"thought": "OPH-C2 is full until 14 October. First bookable slot "
                    "inside the window is 2026-10-14 11:20. Book it - this is "
                    "the irreversible step, so it goes through the gate.",
         "calls": [("book_slot", {"clinic": "OPH-C2", "date": "2026-10-14",
                                  "time": "11:20", "referral_id": "REF-5602"})]},

        {"final": {
            "decision": "book",
            "booked": {"clinic": "OPH-C2", "date": "2026-10-14", "time": "11:20"},
            "reason": "Urgency band routine, so an 8-week window from as_of "
                      "2026-09-09 closing 2026-11-04; booked at 5 weeks. "
                      "VF-01 present. No existing OPH appointment for P-1180. "
                      "OPH-C2 was full until 2026-10-14.",
         },
         "thought": "Record the band, the window, the tests and the duplicate "
                    "check - the answer key asks for all four."},
    ],

    # ---------------------------------------------------------------
    # D7 BASELINE SET (Phase 2 Step 1) - five more hand-scripted,
    # answer-key-verified cases, written the same way as REF-5602 above,
    # so the turn distribution below is measured on more than one case.
    # ---------------------------------------------------------------
    "REF-5750": [
        {"thought": "Fetch the referral.",
         "calls": [("get_referral", {"referral_id": "REF-5750"})]},
        {"thought": "Criteria and patient depend on nothing but the referral.",
         "calls": [("check_referral_criteria", {"specialty": "OPH", "referral_id": "REF-5750"}),
                   ("lookup_patient", {"patient_id": "P-1250"})]},
        {"thought": "Routine, 8-week window from as_of 2026-09-09. Query it.",
         "calls": [("get_clinic_slots", {"specialty": "OPH", "band": "routine",
                                         "from": "2026-09-09", "to": "2026-11-04"})]},
        {"thought": "OPH-C4 is the first bookable slot in the window.",
         "calls": [("book_slot", {"clinic": "OPH-C4", "date": "2026-10-07",
                                  "time": "09:00", "referral_id": "REF-5750"})]},
        {"final": {"decision": "book",
                  "booked": {"clinic": "OPH-C4", "date": "2026-10-07", "time": "09:00"},
                  "reason": "Routine band, 8-week window. VF-01 present. No "
                            "existing OPH appointment for P-1250."},
         "thought": "book"},
    ],

    "REF-5764": [
        {"thought": "Fetch the referral.",
         "calls": [("get_referral", {"referral_id": "REF-5764"})]},
        {"thought": "Criteria and patient depend on nothing but the referral.",
         "calls": [("check_referral_criteria", {"specialty": "ORT", "referral_id": "REF-5764"}),
                   ("lookup_patient", {"patient_id": "P-1264"})]},
        {"thought": "Urgent, 2-week window from as_of 2026-09-09. Query it.",
         "calls": [("get_clinic_slots", {"specialty": "ORT", "band": "urgent",
                                         "from": "2026-09-09", "to": "2026-09-23"})]},
        {"thought": "ORT-C18 is the first bookable slot in the window.",
         "calls": [("book_slot", {"clinic": "ORT-C18", "date": "2026-09-16",
                                  "time": "11:30", "referral_id": "REF-5764"})]},
        {"final": {"decision": "book",
                  "booked": {"clinic": "ORT-C18", "date": "2026-09-16", "time": "11:30"},
                  "reason": "Urgent band, 2-week window. XR-KNEE present. No "
                            "existing ORT appointment for P-1264."},
         "thought": "book"},
    ],

    "REF-5766": [
        {"thought": "Fetch the referral.",
         "calls": [("get_referral", {"referral_id": "REF-5766"})]},
        {"thought": "Criteria and patient depend on nothing but the referral.",
         "calls": [("check_referral_criteria", {"specialty": "OPH", "referral_id": "REF-5766"}),
                   ("lookup_patient", {"patient_id": "P-1266"})]},
        {"thought": "Soon, 4-week window from as_of 2026-09-09. Query it.",
         "calls": [("get_clinic_slots", {"specialty": "OPH", "band": "soon",
                                         "from": "2026-09-09", "to": "2026-10-07"})]},
        {"thought": "OPH-C20 is the first bookable slot in the window.",
         "calls": [("book_slot", {"clinic": "OPH-C20", "date": "2026-09-23",
                                  "time": "10:00", "referral_id": "REF-5766"})]},
        {"final": {"decision": "book",
                  "booked": {"clinic": "OPH-C20", "date": "2026-09-23", "time": "10:00"},
                  "reason": "Soon band, 4-week window. VF-01 present. No "
                            "existing OPH appointment for P-1266."},
         "thought": "book"},
    ],

    "REF-5590": [
        {"thought": "Fetch the referral - the brief's worked example.",
         "calls": [("get_referral", {"referral_id": "REF-5590"})]},
        {"thought": "Criteria and patient depend on nothing but the referral.",
         "calls": [("check_referral_criteria", {"specialty": "OPH", "referral_id": "REF-5590"}),
                   ("lookup_patient", {"patient_id": "P-1192"})]},
        {"final": {"decision": "escalate", "trigger": "red_flag_term",
                  "reason": "Red-flag term 'sudden visual loss' matched. VF-01 "
                            "is attached and an urgent slot existed on "
                            "2026-09-15 - neither saves it; escalate to the "
                            "triage nurse."},
         "thought": "a red flag ends the run; it is not a reason to book sooner"},
    ],

    "REF-5772": [
        {"thought": "Fetch the referral.",
         "calls": [("get_referral", {"referral_id": "REF-5772"})]},
        {"thought": "Criteria and patient depend on nothing but the referral.",
         "calls": [("check_referral_criteria", {"specialty": "ENT", "referral_id": "REF-5772"}),
                   ("lookup_patient", {"patient_id": "P-1272"})]},
        {"final": {"decision": "request_information",
                  "reason": "NASO-02 (nasendoscopy report) is mandatory for ENT "
                            "and missing; AUD-01 was attached but does not "
                            "satisfy that requirement."},
         "thought": "cannot book without the mandatory test"},
    ],

    # ---------------------------------------------------------------
    # PROBLEM A · CLM-8842 - the partly payable claim from Appendix A.
    # Three lines, one of them excluded, one needing a pre-authorisation.
    # ---------------------------------------------------------------
    "CLM-8842": [
        {"thought": "Turn 1 must run alone: everything else needs the member, "
                    "the hospital and the LINE ITEMS this returns.",
         "calls": [("get_claim", {"claim_id": "CLM-8842"})]},

        {"thought": "Now five calls that depend on nothing but that record. "
                    "The policy, the hospital, and one coverage check PER LINE "
                    "- three lines, three checks. All independent, so one turn.",
         "calls": [("lookup_policy", {"member_id": "M-2214"}),
                   ("check_coverage", {"code": "47120", "policy_id": "POL-3310"}),
                   ("check_coverage", {"code": "31255", "policy_id": "POL-3310"}),
                   ("check_coverage", {"code": "62480", "policy_id": "POL-3310"}),
                   ("lookup_hospital", {"hospital_id": "H-114"})]},

        {"thought": "This one CANNOT join the turn above: I did not know which "
                    "line needed a pre-authorisation until coverage answered. "
                    "That is the dependency rule. Only 62480 needs one.",
         "calls": [("get_preauthorisation", {"member_id": "M-2214",
                                             "procedure_code": "62480",
                                             "date_of_service": "2026-09-02"})]},

        {"thought": "A disposition for every line, then send. This is the "
                    "irreversible step, so it goes through the gate - and it "
                    "is a turn like any other.",
         "calls": [("issue_decision_letter", {
             "claim_id": "CLM-8842",
             "decision": "approve_in_principle",
             "lines_resolved": 3,
             "approved_total": 2180,
             "refused_total": 300})]},

        {"final": {
            "decision": "approve_in_principle",
            "reason": "3 lines. 47120 covered (1400). 62480 covered, PA-5521 "
                      "cited, valid on 2026-09-02 (780). 31255 refused under "
                      "EX-14 cosmetic dermatology (300). approved_total 2180, "
                      "refused_total 300. H-114 is on panel.",
         },
         "thought": "Eight calls, four turns. Not an approve and not a "
                    "decline: one decision letter covering both."},
    ],
}


class ScriptedBackend:
    """Replays SCRIPTS[case_id]. Deterministic, free, offline."""

    name = "scripted"

    def __init__(self, case_id):
        if case_id not in SCRIPTS:
            raise SystemExit(
                "\n  No script for case %r.\n"
                "  The scripted backend replays moves you wrote down; it does\n"
                "  not invent them. Two ways forward:\n"
                "    1. add %r to SCRIPTS in backends.py, or\n"
                "    2. set BACKEND = \"live\" in config.py (this costs money).\n"
                "  Scripted cases so far: %s\n"
                % (case_id, case_id, ", ".join(sorted(SCRIPTS))))
        self.steps = SCRIPTS[case_id]
        self.i = 0

    def next_move(self, transcript):
        """`transcript` is ignored on purpose - a script does not react.
        That is what makes it reproducible."""
        if self.i >= len(self.steps):
            return {"final": {"decision": "escalate",
                              "reason": "script ended without a conclusion"},
                    "thought": "script exhausted"}
        step = self.steps[self.i]
        self.i += 1
        return step

    # Token counts on the scripted backend are ESTIMATES, so your cost
    # arithmetic has something to chew on. They are not measurements and
    # you must not report them as such - D6 wants MEASURED counts, which
    # means the live battery.
    @staticmethod
    def token_estimate(transcript):
        return 1800 + 600 * len(transcript), 120


# =====================================================================
# LIVE
# =====================================================================
class LiveBackend:
    """Real model through OpenRouter. Costs money. D5(b) only."""

    name = "live"

    def __init__(self, case_id, tool_descriptors, system_prompt):
        self.case_id = case_id
        self.tools = tool_descriptors
        self.system_prompt = system_prompt

    def next_move(self, transcript):
        messages = [{"role": "system", "content": self.system_prompt}]
        for entry in transcript:
            messages.append({"role": entry["role"], "content": entry["content"]})
        raw = _live_call(messages)
        return _parse_move(raw)

    @staticmethod
    def token_estimate(transcript):
        # Replace with the usage numbers the API returns. Estimating here
        # and calling it measured is the mistake D6 punishes.
        return 0, 0


def _parse_move(text):
    """The model must answer in JSON. Anything else is a run you cannot
    grade, so say so loudly rather than guessing."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"final": {"decision": "escalate",
                          "reason": "model did not return parseable JSON"},
                "thought": "unparseable: %s" % text[:200]}


def _live_call(messages):
    """>>> THE ONLY FUNCTION IN THIS REPOSITORY THAT KNOWS A VENDOR <<<

    Everything else speaks in terms of moves and transcripts. Swapping
    vendor means rewriting this one function, and changing MODEL and
    BASE_URL in config.py. Nothing else.
    """
    if not config.API_KEY:
        raise SystemExit(
            "\n  BACKEND is 'live' but OPENROUTER_API_KEY is not set.\n"
            "    export OPENROUTER_API_KEY='sk-or-...'\n"
            "  Or set BACKEND = 'scripted' in config.py, which is free.\n")
    body = json.dumps({
        "model": config.MODEL,
        "messages": messages,
        "temperature": 0,
    }).encode()
    req = urllib.request.Request(
        config.BASE_URL.rstrip("/") + "/chat/completions",
        data=body,
        headers={"Authorization": "Bearer " + config.API_KEY,
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        payload = json.load(r)
    return payload["choices"][0]["message"]["content"]


def make_backend(case_id, tool_descriptors=None, system_prompt=""):
    if config.BACKEND == "scripted":
        return ScriptedBackend(case_id)
    if config.BACKEND == "live":
        return LiveBackend(case_id, tool_descriptors or [], system_prompt)
    raise SystemExit("BACKEND must be 'scripted' or 'live', not %r"
                     % config.BACKEND)

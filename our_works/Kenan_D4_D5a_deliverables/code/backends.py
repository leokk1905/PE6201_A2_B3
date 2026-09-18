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

    "REF-5750": [
        {"thought": "Fetch referral record.",
         "calls": [("get_referral", {"referral_id": "REF-5750"})]},
        {"thought": "Check OPH criteria and patient P-1250 record.",
         "calls": [("check_referral_criteria", {"specialty": "OPH", "referral_id": "REF-5750"}), ("lookup_patient", {"patient_id": "P-1250"})]},
        {"thought": "Query routine OPH slots within the legal window.",
         "calls": [("get_clinic_slots", {"specialty": "OPH", "band": "routine", "from": "2026-09-09", "to": "2026-11-04"})]},
        {"thought": "Book OPH-C4 on 2026-10-07 at 09:00 via the gate.",
         "calls": [("book_slot", {"clinic": "OPH-C4", "date": "2026-10-07", "time": "09:00", "referral_id": "REF-5750"})]},
        {"final": {"decision": "book", "booked": {"clinic": "OPH-C4", "date": "2026-10-07", "time": "09:00"}, "reason": "urgency band routine and the 8-week window. VF-01 present. no existing OPH appointment for P-1250."},
         "thought": "Record final outcome: book."}
    ],
    "REF-5751": [
        {"thought": "Fetch referral record.",
         "calls": [("get_referral", {"referral_id": "REF-5751"})]},
        {"thought": "Check CARD criteria and patient P-1251 record.",
         "calls": [("check_referral_criteria", {"specialty": "CARD", "referral_id": "REF-5751"}), ("lookup_patient", {"patient_id": "P-1251"})]},
        {"thought": "Query routine CARD slots within the legal window.",
         "calls": [("get_clinic_slots", {"specialty": "CARD", "band": "routine", "from": "2026-09-09", "to": "2026-11-04"})]},
        {"thought": "Book CARD-C5 on 2026-10-14 at 10:20 via the gate.",
         "calls": [("book_slot", {"clinic": "CARD-C5", "date": "2026-10-14", "time": "10:20", "referral_id": "REF-5751"})]},
        {"final": {"decision": "book", "booked": {"clinic": "CARD-C5", "date": "2026-10-14", "time": "10:20"}, "reason": "urgency band routine and the 8-week window. ECG-12, BNP-01 present. no existing CARD appointment for P-1251."},
         "thought": "Record final outcome: book."}
    ],
    "REF-5752": [
        {"thought": "Fetch referral record.",
         "calls": [("get_referral", {"referral_id": "REF-5752"})]},
        {"thought": "Check ORT criteria and patient P-1252 record.",
         "calls": [("check_referral_criteria", {"specialty": "ORT", "referral_id": "REF-5752"}), ("lookup_patient", {"patient_id": "P-1252"})]},
        {"thought": "Query routine ORT slots within the legal window.",
         "calls": [("get_clinic_slots", {"specialty": "ORT", "band": "routine", "from": "2026-09-09", "to": "2026-11-04"})]},
        {"thought": "Book ORT-C6 on 2026-10-21 at 11:40 via the gate.",
         "calls": [("book_slot", {"clinic": "ORT-C6", "date": "2026-10-21", "time": "11:40", "referral_id": "REF-5752"})]},
        {"final": {"decision": "book", "booked": {"clinic": "ORT-C6", "date": "2026-10-21", "time": "11:40"}, "reason": "urgency band routine and the 8-week window. XR-KNEE present. no existing ORT appointment for P-1252."},
         "thought": "Record final outcome: book."}
    ],
    "REF-5753": [
        {"thought": "Fetch referral record.",
         "calls": [("get_referral", {"referral_id": "REF-5753"})]},
        {"thought": "Check DER criteria and patient P-1253 record.",
         "calls": [("check_referral_criteria", {"specialty": "DER", "referral_id": "REF-5753"}), ("lookup_patient", {"patient_id": "P-1253"})]},
        {"thought": "Query routine DER slots within the legal window.",
         "calls": [("get_clinic_slots", {"specialty": "DER", "band": "routine", "from": "2026-09-09", "to": "2026-11-04"})]},
        {"thought": "Book DER-C7 on 2026-10-07 at 12:00 via the gate.",
         "calls": [("book_slot", {"clinic": "DER-C7", "date": "2026-10-07", "time": "12:00", "referral_id": "REF-5753"})]},
        {"final": {"decision": "book", "booked": {"clinic": "DER-C7", "date": "2026-10-07", "time": "12:00"}, "reason": "urgency band routine and the 8-week window. no mandatory tests for DER. no existing DER appointment for P-1253."},
         "thought": "Record final outcome: book."}
    ],
    "REF-5754": [
        {"thought": "Fetch referral record.",
         "calls": [("get_referral", {"referral_id": "REF-5754"})]},
        {"thought": "Check ENT criteria and patient P-1254 record.",
         "calls": [("check_referral_criteria", {"specialty": "ENT", "referral_id": "REF-5754"}), ("lookup_patient", {"patient_id": "P-1254"})]},
        {"thought": "Query routine ENT slots within the legal window.",
         "calls": [("get_clinic_slots", {"specialty": "ENT", "band": "routine", "from": "2026-09-09", "to": "2026-11-04"})]},
        {"thought": "Book ENT-C8 on 2026-10-14 at 13:20 via the gate.",
         "calls": [("book_slot", {"clinic": "ENT-C8", "date": "2026-10-14", "time": "13:20", "referral_id": "REF-5754"})]},
        {"final": {"decision": "book", "booked": {"clinic": "ENT-C8", "date": "2026-10-14", "time": "13:20"}, "reason": "urgency band routine and the 8-week window. AUD-01, NASO-02 present. no existing ENT appointment for P-1254."},
         "thought": "Record final outcome: book."}
    ],
    "REF-5755": [
        {"thought": "Fetch referral record.",
         "calls": [("get_referral", {"referral_id": "REF-5755"})]},
        {"thought": "Check OPH criteria and patient P-1255 record.",
         "calls": [("check_referral_criteria", {"specialty": "OPH", "referral_id": "REF-5755"}), ("lookup_patient", {"patient_id": "P-1255"})]},
        {"thought": "Query routine OPH slots within the legal window.",
         "calls": [("get_clinic_slots", {"specialty": "OPH", "band": "routine", "from": "2026-09-09", "to": "2026-11-04"})]},
        {"thought": "Book OPH-C9 on 2026-10-21 at 14:40 via the gate.",
         "calls": [("book_slot", {"clinic": "OPH-C9", "date": "2026-10-21", "time": "14:40", "referral_id": "REF-5755"})]},
        {"final": {"decision": "book", "booked": {"clinic": "OPH-C9", "date": "2026-10-21", "time": "14:40"}, "reason": "urgency band routine and the 8-week window. VF-01 present. no existing OPH appointment for P-1255."},
         "thought": "Record final outcome: book."}
    ],
    "REF-5756": [
        {"thought": "Fetch referral record.",
         "calls": [("get_referral", {"referral_id": "REF-5756"})]},
        {"thought": "Check CARD criteria and patient P-1256 record.",
         "calls": [("check_referral_criteria", {"specialty": "CARD", "referral_id": "REF-5756"}), ("lookup_patient", {"patient_id": "P-1256"})]},
        {"thought": "Query routine CARD slots within the legal window.",
         "calls": [("get_clinic_slots", {"specialty": "CARD", "band": "routine", "from": "2026-09-09", "to": "2026-11-04"})]},
        {"thought": "Book CARD-C10 on 2026-10-07 at 09:00 via the gate.",
         "calls": [("book_slot", {"clinic": "CARD-C10", "date": "2026-10-07", "time": "09:00", "referral_id": "REF-5756"})]},
        {"final": {"decision": "book", "booked": {"clinic": "CARD-C10", "date": "2026-10-07", "time": "09:00"}, "reason": "urgency band routine and the 8-week window. ECG-12, BNP-01 present. no existing CARD appointment for P-1256."},
         "thought": "Record final outcome: book."}
    ],
    "REF-5757": [
        {"thought": "Fetch referral record.",
         "calls": [("get_referral", {"referral_id": "REF-5757"})]},
        {"thought": "Check ORT criteria and patient P-1257 record.",
         "calls": [("check_referral_criteria", {"specialty": "ORT", "referral_id": "REF-5757"}), ("lookup_patient", {"patient_id": "P-1257"})]},
        {"thought": "Query routine ORT slots within the legal window.",
         "calls": [("get_clinic_slots", {"specialty": "ORT", "band": "routine", "from": "2026-09-09", "to": "2026-11-04"})]},
        {"thought": "Book ORT-C11 on 2026-10-14 at 10:20 via the gate.",
         "calls": [("book_slot", {"clinic": "ORT-C11", "date": "2026-10-14", "time": "10:20", "referral_id": "REF-5757"})]},
        {"final": {"decision": "book", "booked": {"clinic": "ORT-C11", "date": "2026-10-14", "time": "10:20"}, "reason": "urgency band routine and the 8-week window. XR-KNEE present. no existing ORT appointment for P-1257."},
         "thought": "Record final outcome: book."}
    ],
    "REF-5758": [
        {"thought": "Fetch referral record.",
         "calls": [("get_referral", {"referral_id": "REF-5758"})]},
        {"thought": "Check DER criteria and patient P-1258 record.",
         "calls": [("check_referral_criteria", {"specialty": "DER", "referral_id": "REF-5758"}), ("lookup_patient", {"patient_id": "P-1258"})]},
        {"thought": "Query routine DER slots within the legal window.",
         "calls": [("get_clinic_slots", {"specialty": "DER", "band": "routine", "from": "2026-09-09", "to": "2026-11-04"})]},
        {"thought": "Book DER-C12 on 2026-10-21 at 11:40 via the gate.",
         "calls": [("book_slot", {"clinic": "DER-C12", "date": "2026-10-21", "time": "11:40", "referral_id": "REF-5758"})]},
        {"final": {"decision": "book", "booked": {"clinic": "DER-C12", "date": "2026-10-21", "time": "11:40"}, "reason": "urgency band routine and the 8-week window. no mandatory tests for DER. no existing DER appointment for P-1258."},
         "thought": "Record final outcome: book."}
    ],
    "REF-5759": [
        {"thought": "Fetch referral record.",
         "calls": [("get_referral", {"referral_id": "REF-5759"})]},
        {"thought": "Check ENT criteria and patient P-1259 record.",
         "calls": [("check_referral_criteria", {"specialty": "ENT", "referral_id": "REF-5759"}), ("lookup_patient", {"patient_id": "P-1259"})]},
        {"thought": "Query routine ENT slots within the legal window.",
         "calls": [("get_clinic_slots", {"specialty": "ENT", "band": "routine", "from": "2026-09-09", "to": "2026-11-04"})]},
        {"thought": "Book ENT-C13 on 2026-10-07 at 12:00 via the gate.",
         "calls": [("book_slot", {"clinic": "ENT-C13", "date": "2026-10-07", "time": "12:00", "referral_id": "REF-5759"})]},
        {"final": {"decision": "book", "booked": {"clinic": "ENT-C13", "date": "2026-10-07", "time": "12:00"}, "reason": "urgency band routine and the 8-week window. AUD-01, NASO-02 present. no existing ENT appointment for P-1259."},
         "thought": "Record final outcome: book."}
    ],
    "REF-5760": [
        {"thought": "Fetch referral record.",
         "calls": [("get_referral", {"referral_id": "REF-5760"})]},
        {"thought": "Check OPH criteria and patient P-1260 record.",
         "calls": [("check_referral_criteria", {"specialty": "OPH", "referral_id": "REF-5760"}), ("lookup_patient", {"patient_id": "P-1260"})]},
        {"thought": "Query routine OPH slots within the legal window.",
         "calls": [("get_clinic_slots", {"specialty": "OPH", "band": "routine", "from": "2026-09-09", "to": "2026-11-04"})]},
        {"thought": "Book OPH-C14 on 2026-10-14 at 13:20 via the gate.",
         "calls": [("book_slot", {"clinic": "OPH-C14", "date": "2026-10-14", "time": "13:20", "referral_id": "REF-5760"})]},
        {"final": {"decision": "book", "booked": {"clinic": "OPH-C14", "date": "2026-10-14", "time": "13:20"}, "reason": "urgency band routine and the 8-week window. VF-01 present. no existing OPH appointment for P-1260."},
         "thought": "Record final outcome: book."}
    ],
    "REF-5761": [
        {"thought": "Fetch referral record.",
         "calls": [("get_referral", {"referral_id": "REF-5761"})]},
        {"thought": "Check CARD criteria and patient P-1261 record.",
         "calls": [("check_referral_criteria", {"specialty": "CARD", "referral_id": "REF-5761"}), ("lookup_patient", {"patient_id": "P-1261"})]},
        {"thought": "Query routine CARD slots within the legal window.",
         "calls": [("get_clinic_slots", {"specialty": "CARD", "band": "routine", "from": "2026-09-09", "to": "2026-11-04"})]},
        {"thought": "Book CARD-C15 on 2026-10-21 at 14:40 via the gate.",
         "calls": [("book_slot", {"clinic": "CARD-C15", "date": "2026-10-21", "time": "14:40", "referral_id": "REF-5761"})]},
        {"final": {"decision": "book", "booked": {"clinic": "CARD-C15", "date": "2026-10-21", "time": "14:40"}, "reason": "urgency band routine and the 8-week window. ECG-12, BNP-01 present. no existing CARD appointment for P-1261."},
         "thought": "Record final outcome: book."}
    ],
    "REF-5762": [
        {"thought": "Fetch referral record.",
         "calls": [("get_referral", {"referral_id": "REF-5762"})]},
        {"thought": "Check OPH criteria and patient P-1262 record.",
         "calls": [("check_referral_criteria", {"specialty": "OPH", "referral_id": "REF-5762"}), ("lookup_patient", {"patient_id": "P-1262"})]},
        {"thought": "Query routine OPH slots within the legal window.",
         "calls": [("get_clinic_slots", {"specialty": "OPH", "band": "routine", "from": "2026-09-09", "to": "2026-11-04"})]},
        {"thought": "Book OPH-C16 on 2026-09-16 at 09:30 via the gate.",
         "calls": [("book_slot", {"clinic": "OPH-C16", "date": "2026-09-16", "time": "09:30", "referral_id": "REF-5762"})]},
        {"final": {"decision": "book", "booked": {"clinic": "OPH-C16", "date": "2026-09-16", "time": "09:30"}, "reason": "urgency band urgent and the 2-week window. VF-01 present. no existing OPH appointment for P-1262."},
         "thought": "Record final outcome: book."}
    ],
    "REF-5763": [
        {"thought": "Fetch referral record.",
         "calls": [("get_referral", {"referral_id": "REF-5763"})]},
        {"thought": "Check CARD criteria and patient P-1263 record.",
         "calls": [("check_referral_criteria", {"specialty": "CARD", "referral_id": "REF-5763"}), ("lookup_patient", {"patient_id": "P-1263"})]},
        {"thought": "Query routine CARD slots within the legal window.",
         "calls": [("get_clinic_slots", {"specialty": "CARD", "band": "routine", "from": "2026-09-09", "to": "2026-11-04"})]},
        {"thought": "Book CARD-C17 on 2026-09-16 at 10:30 via the gate.",
         "calls": [("book_slot", {"clinic": "CARD-C17", "date": "2026-09-16", "time": "10:30", "referral_id": "REF-5763"})]},
        {"final": {"decision": "book", "booked": {"clinic": "CARD-C17", "date": "2026-09-16", "time": "10:30"}, "reason": "urgency band urgent and the 2-week window. ECG-12, BNP-01 present. no existing CARD appointment for P-1263."},
         "thought": "Record final outcome: book."}
    ],
    "REF-5764": [
        {"thought": "Fetch referral record.",
         "calls": [("get_referral", {"referral_id": "REF-5764"})]},
        {"thought": "Check ORT criteria and patient P-1264 record.",
         "calls": [("check_referral_criteria", {"specialty": "ORT", "referral_id": "REF-5764"}), ("lookup_patient", {"patient_id": "P-1264"})]},
        {"thought": "Query routine ORT slots within the legal window.",
         "calls": [("get_clinic_slots", {"specialty": "ORT", "band": "routine", "from": "2026-09-09", "to": "2026-11-04"})]},
        {"thought": "Book ORT-C18 on 2026-09-16 at 11:30 via the gate.",
         "calls": [("book_slot", {"clinic": "ORT-C18", "date": "2026-09-16", "time": "11:30", "referral_id": "REF-5764"})]},
        {"final": {"decision": "book", "booked": {"clinic": "ORT-C18", "date": "2026-09-16", "time": "11:30"}, "reason": "urgency band urgent and the 2-week window. XR-KNEE present. no existing ORT appointment for P-1264."},
         "thought": "Record final outcome: book."}
    ],
    "REF-5765": [
        {"thought": "Fetch referral record.",
         "calls": [("get_referral", {"referral_id": "REF-5765"})]},
        {"thought": "Check DER criteria and patient P-1265 record.",
         "calls": [("check_referral_criteria", {"specialty": "DER", "referral_id": "REF-5765"}), ("lookup_patient", {"patient_id": "P-1265"})]},
        {"thought": "Query routine DER slots within the legal window.",
         "calls": [("get_clinic_slots", {"specialty": "DER", "band": "routine", "from": "2026-09-09", "to": "2026-11-04"})]},
        {"thought": "Book DER-C19 on 2026-09-16 at 12:30 via the gate.",
         "calls": [("book_slot", {"clinic": "DER-C19", "date": "2026-09-16", "time": "12:30", "referral_id": "REF-5765"})]},
        {"final": {"decision": "book", "booked": {"clinic": "DER-C19", "date": "2026-09-16", "time": "12:30"}, "reason": "urgency band urgent and the 2-week window.  present. no existing DER appointment for P-1265."},
         "thought": "Record final outcome: book."}
    ],
    "REF-5766": [
        {"thought": "Fetch referral record.",
         "calls": [("get_referral", {"referral_id": "REF-5766"})]},
        {"thought": "Check OPH criteria and patient P-1266 record.",
         "calls": [("check_referral_criteria", {"specialty": "OPH", "referral_id": "REF-5766"}), ("lookup_patient", {"patient_id": "P-1266"})]},
        {"thought": "Query routine OPH slots within the legal window.",
         "calls": [("get_clinic_slots", {"specialty": "OPH", "band": "routine", "from": "2026-09-09", "to": "2026-11-04"})]},
        {"thought": "Book OPH-C20 on 2026-09-23 at 10:00 via the gate.",
         "calls": [("book_slot", {"clinic": "OPH-C20", "date": "2026-09-23", "time": "10:00", "referral_id": "REF-5766"})]},
        {"final": {"decision": "book", "booked": {"clinic": "OPH-C20", "date": "2026-09-23", "time": "10:00"}, "reason": "urgency band soon and the 4-week window. VF-01 present. no existing OPH appointment for P-1266."},
         "thought": "Record final outcome: book."}
    ],
    "REF-5767": [
        {"thought": "Fetch referral record.",
         "calls": [("get_referral", {"referral_id": "REF-5767"})]},
        {"thought": "Check CARD criteria and patient P-1267 record.",
         "calls": [("check_referral_criteria", {"specialty": "CARD", "referral_id": "REF-5767"}), ("lookup_patient", {"patient_id": "P-1267"})]},
        {"thought": "Query routine CARD slots within the legal window.",
         "calls": [("get_clinic_slots", {"specialty": "CARD", "band": "routine", "from": "2026-09-09", "to": "2026-11-04"})]},
        {"thought": "Book CARD-C21 on 2026-09-30 at 11:00 via the gate.",
         "calls": [("book_slot", {"clinic": "CARD-C21", "date": "2026-09-30", "time": "11:00", "referral_id": "REF-5767"})]},
        {"final": {"decision": "book", "booked": {"clinic": "CARD-C21", "date": "2026-09-30", "time": "11:00"}, "reason": "urgency band soon and the 4-week window. ECG-12, BNP-01 present. no existing CARD appointment for P-1267."},
         "thought": "Record final outcome: book."}
    ],
    "REF-5768": [
        {"thought": "Fetch referral record.",
         "calls": [("get_referral", {"referral_id": "REF-5768"})]},
        {"thought": "Check ORT criteria and patient P-1268 record.",
         "calls": [("check_referral_criteria", {"specialty": "ORT", "referral_id": "REF-5768"}), ("lookup_patient", {"patient_id": "P-1268"})]},
        {"thought": "Query routine ORT slots within the legal window.",
         "calls": [("get_clinic_slots", {"specialty": "ORT", "band": "routine", "from": "2026-09-09", "to": "2026-11-04"})]},
        {"thought": "Book ORT-C22 on 2026-09-23 at 12:00 via the gate.",
         "calls": [("book_slot", {"clinic": "ORT-C22", "date": "2026-09-23", "time": "12:00", "referral_id": "REF-5768"})]},
        {"final": {"decision": "book", "booked": {"clinic": "ORT-C22", "date": "2026-09-23", "time": "12:00"}, "reason": "urgency band soon and the 4-week window. XR-KNEE present. no existing ORT appointment for P-1268."},
         "thought": "Record final outcome: book."}
    ],
    "REF-5769": [
        {"thought": "Fetch referral record.",
         "calls": [("get_referral", {"referral_id": "REF-5769"})]},
        {"thought": "Check ENT criteria and patient P-1269 record.",
         "calls": [("check_referral_criteria", {"specialty": "ENT", "referral_id": "REF-5769"}), ("lookup_patient", {"patient_id": "P-1269"})]},
        {"thought": "Query routine ENT slots within the legal window.",
         "calls": [("get_clinic_slots", {"specialty": "ENT", "band": "routine", "from": "2026-09-09", "to": "2026-11-04"})]},
        {"thought": "Book ENT-C23 on 2026-09-30 at 13:00 via the gate.",
         "calls": [("book_slot", {"clinic": "ENT-C23", "date": "2026-09-30", "time": "13:00", "referral_id": "REF-5769"})]},
        {"final": {"decision": "book", "booked": {"clinic": "ENT-C23", "date": "2026-09-30", "time": "13:00"}, "reason": "urgency band soon and the 4-week window. AUD-01, NASO-02 present. no existing ENT appointment for P-1269."},
         "thought": "Record final outcome: book."}
    ],
    "REF-5770": [
        {"thought": "Fetch referral record.",
         "calls": [("get_referral", {"referral_id": "REF-5770"})]},
        {"thought": "Check OPH criteria and patient P-1270 record.",
         "calls": [("check_referral_criteria", {"specialty": "OPH", "referral_id": "REF-5770"}), ("lookup_patient", {"patient_id": "P-1270"})]},
        {"final": {"decision": "request_information", "missing": "required pre-referral test", "reason": "VF-01 named. the OPH rule that requires it. that IOP-03 was attached but does not satisfy it."},
         "thought": "Record final outcome: request_information."}
    ],
    "REF-5771": [
        {"thought": "Fetch referral record.",
         "calls": [("get_referral", {"referral_id": "REF-5771"})]},
        {"thought": "Check CARD criteria and patient P-1271 record.",
         "calls": [("check_referral_criteria", {"specialty": "CARD", "referral_id": "REF-5771"}), ("lookup_patient", {"patient_id": "P-1271"})]},
        {"final": {"decision": "request_information", "missing": "required pre-referral test", "reason": "BNP-01 named. the CARD rule that requires it. that ECG-12 was attached but does not satisfy it."},
         "thought": "Record final outcome: request_information."}
    ],
    "REF-5772": [
        {"thought": "Fetch referral record.",
         "calls": [("get_referral", {"referral_id": "REF-5772"})]},
        {"thought": "Check ENT criteria and patient P-1272 record.",
         "calls": [("check_referral_criteria", {"specialty": "ENT", "referral_id": "REF-5772"}), ("lookup_patient", {"patient_id": "P-1272"})]},
        {"final": {"decision": "request_information", "missing": "required pre-referral test", "reason": "NASO-02 named. the ENT rule that requires it. that AUD-01 was attached but does not satisfy it."},
         "thought": "Record final outcome: request_information."}
    ],
    "REF-5773": [
        {"thought": "Fetch referral record.",
         "calls": [("get_referral", {"referral_id": "REF-5773"})]},
        {"thought": "Check ORT criteria and patient P-1273 record.",
         "calls": [("check_referral_criteria", {"specialty": "ORT", "referral_id": "REF-5773"}), ("lookup_patient", {"patient_id": "P-1273"})]},
        {"final": {"decision": "request_information", "missing": "required pre-referral test", "reason": "XR-KNEE named. the ORT rule that requires it."},
         "thought": "Record final outcome: request_information."}
    ],
    "REF-5774": [
        {"thought": "Fetch referral record.",
         "calls": [("get_referral", {"referral_id": "REF-5774"})]},
        {"thought": "Check CARD criteria and patient P-1274 record.",
         "calls": [("check_referral_criteria", {"specialty": "CARD", "referral_id": "REF-5774"}), ("lookup_patient", {"patient_id": "P-1274"})]},
        {"final": {"decision": "request_information", "missing": "required pre-referral test", "reason": "mandatory tests named. the CARD rule that requires them."},
         "thought": "Record final outcome: request_information."}
    ],
    "REF-5775": [
        {"thought": "Fetch referral record.",
         "calls": [("get_referral", {"referral_id": "REF-5775"})]},
        {"thought": "Check ENT criteria and patient P-1275 record.",
         "calls": [("check_referral_criteria", {"specialty": "ENT", "referral_id": "REF-5775"}), ("lookup_patient", {"patient_id": "P-1275"})]},
        {"final": {"decision": "request_information", "missing": "required pre-referral test", "reason": "mandatory tests named. the ENT rule that requires them."},
         "thought": "Record final outcome: request_information."}
    ],
    "REF-5776": [
        {"thought": "Fetch referral record.",
         "calls": [("get_referral", {"referral_id": "REF-5776"})]},
        {"thought": "Check ORT criteria and patient P-1276 record.",
         "calls": [("check_referral_criteria", {"specialty": "ORT", "referral_id": "REF-5776"}), ("lookup_patient", {"patient_id": "P-1276"})]},
        {"final": {"decision": "request_information", "missing": "required pre-referral test", "reason": "mandatory tests named. the ORT rule that requires them."},
         "thought": "Record final outcome: request_information."}
    ],
    "REF-5777": [
        {"thought": "Fetch referral record.",
         "calls": [("get_referral", {"referral_id": "REF-5777"})]},
        {"thought": "Check OPH criteria and patient P-1277 record.",
         "calls": [("check_referral_criteria", {"specialty": "OPH", "referral_id": "REF-5777"}), ("lookup_patient", {"patient_id": "P-1277"})]},
        {"final": {"decision": "escalate", "trigger": "red_flag_term", "reason": "the red-flag term \"sudden visual loss\". escalate_to triage nurse. that this is a OPH red flag."},
         "thought": "Record final outcome: escalate."}
    ],
    "REF-5778": [
        {"thought": "Fetch referral record.",
         "calls": [("get_referral", {"referral_id": "REF-5778"})]},
        {"thought": "Check CARD criteria and patient P-1278 record.",
         "calls": [("check_referral_criteria", {"specialty": "CARD", "referral_id": "REF-5778"}), ("lookup_patient", {"patient_id": "P-1278"})]},
        {"final": {"decision": "escalate", "trigger": "red_flag_term", "reason": "the red-flag term \"syncope on exertion\". escalate_to triage nurse. that this is a CARD red flag."},
         "thought": "Record final outcome: escalate."}
    ],
    "REF-5779": [
        {"thought": "Fetch referral record.",
         "calls": [("get_referral", {"referral_id": "REF-5779"})]},
        {"thought": "Check ORT criteria and patient P-1279 record.",
         "calls": [("check_referral_criteria", {"specialty": "ORT", "referral_id": "REF-5779"}), ("lookup_patient", {"patient_id": "P-1279"})]},
        {"final": {"decision": "escalate", "trigger": "red_flag_term", "reason": "the red-flag term \"saddle anaesthesia\". escalate_to triage nurse. that this is a ORT red flag."},
         "thought": "Record final outcome: escalate."}
    ],
    "REF-5780": [
        {"thought": "Fetch referral record.",
         "calls": [("get_referral", {"referral_id": "REF-5780"})]},
        {"thought": "Check DER criteria and patient P-1280 record.",
         "calls": [("check_referral_criteria", {"specialty": "DER", "referral_id": "REF-5780"}), ("lookup_patient", {"patient_id": "P-1280"})]},
        {"final": {"decision": "escalate", "trigger": "red_flag_term", "reason": "the red-flag term \"ulcerating lesion\". escalate_to triage nurse. that this is a DER red flag."},
         "thought": "Record final outcome: escalate."}
    ],
    "REF-5781": [
        {"thought": "Fetch referral record.",
         "calls": [("get_referral", {"referral_id": "REF-5781"})]},
        {"thought": "Check OPH criteria and patient P-1281 record.",
         "calls": [("check_referral_criteria", {"specialty": "OPH", "referral_id": "REF-5781"}), ("lookup_patient", {"patient_id": "P-1281"})]},
        {"final": {"decision": "escalate", "trigger": "specialty_mismatch", "reason": "that OPH was requested. that the summary describes a card problem. escalate_to triage nurse."},
         "thought": "Record final outcome: escalate."}
    ],
    "REF-5782": [
        {"thought": "Fetch referral record.",
         "calls": [("get_referral", {"referral_id": "REF-5782"})]},
        {"thought": "Check CARD criteria and patient P-1282 record.",
         "calls": [("check_referral_criteria", {"specialty": "CARD", "referral_id": "REF-5782"}), ("lookup_patient", {"patient_id": "P-1282"})]},
        {"final": {"decision": "escalate", "trigger": "specialty_mismatch", "reason": "that CARD was requested. that the summary describes a ort problem. escalate_to triage nurse."},
         "thought": "Record final outcome: escalate."}
    ],
    "REF-5783": [
        {"thought": "Fetch referral record.",
         "calls": [("get_referral", {"referral_id": "REF-5783"})]},
        {"thought": "Check ORT criteria and patient P-1283 record.",
         "calls": [("check_referral_criteria", {"specialty": "ORT", "referral_id": "REF-5783"}), ("lookup_patient", {"patient_id": "P-1283"})]},
        {"final": {"decision": "escalate", "trigger": "specialty_mismatch", "reason": "that ORT was requested. that the summary describes a ent problem. escalate_to triage nurse."},
         "thought": "Record final outcome: escalate."}
    ],
    "REF-5784": [
        {"thought": "Fetch referral record.",
         "calls": [("get_referral", {"referral_id": "REF-5784"})]},
        {"thought": "Check OPH criteria and patient P-1284 record.",
         "calls": [("check_referral_criteria", {"specialty": "OPH", "referral_id": "REF-5784"}), ("lookup_patient", {"patient_id": "P-1284"})]},
        {"final": {"decision": "escalate", "trigger": "duplicate_future_appointment", "reason": "P-1284's existing OPH appointment on 2026-09-30. that it is in the future and in the same specialty."},
         "thought": "Record final outcome: escalate."}
    ],
    "REF-5785": [
        {"thought": "Fetch referral record.",
         "calls": [("get_referral", {"referral_id": "REF-5785"})]},
        {"thought": "Check CARD criteria and patient P-1285 record.",
         "calls": [("check_referral_criteria", {"specialty": "CARD", "referral_id": "REF-5785"}), ("lookup_patient", {"patient_id": "P-1285"})]},
        {"final": {"decision": "escalate", "trigger": "duplicate_future_appointment", "reason": "P-1285's existing CARD appointment on 2026-09-30. that it is in the future and in the same specialty."},
         "thought": "Record final outcome: escalate."}
    ],
    "REF-5786": [
        {"thought": "Fetch referral record.",
         "calls": [("get_referral", {"referral_id": "REF-5786"})]},
        {"thought": "Check ENT criteria and patient P-1286 record.",
         "calls": [("check_referral_criteria", {"specialty": "ENT", "referral_id": "REF-5786"}), ("lookup_patient", {"patient_id": "P-1286"})]},
        {"final": {"decision": "escalate", "trigger": "duplicate_future_appointment", "reason": "P-1286's existing ENT appointment on 2026-09-30. that it is in the future and in the same specialty."},
         "thought": "Record final outcome: escalate."}
    ],
    "REF-5787": [
        {"thought": "Fetch referral record.",
         "calls": [("get_referral", {"referral_id": "REF-5787"})]},
        {"thought": "Check ENT criteria and patient P-1287 record.",
         "calls": [("check_referral_criteria", {"specialty": "ENT", "referral_id": "REF-5787"}), ("lookup_patient", {"patient_id": "P-1287"})]},
        {"thought": "Search urgent ENT slots within the window. No valid slot found.",
         "calls": [("get_clinic_slots", {"specialty": "ENT", "band": "urgent", "from": "2026-09-09", "to": "2026-09-23"})]},
        {"final": {"decision": "escalate", "trigger": "no_slot_in_window", "reason": "urgent band, 2-week window ending 2026-09-23. that ENT has no urgent clinic. that the earliest ENT slot is 2026-10-14, outside the window."},
         "thought": "Record final outcome: escalate."}
    ],
    "REF-5788": [
        {"thought": "Fetch referral record.",
         "calls": [("get_referral", {"referral_id": "REF-5788"})]},
        {"thought": "Check ORT criteria and patient P-1288 record.",
         "calls": [("check_referral_criteria", {"specialty": "ORT", "referral_id": "REF-5788"}), ("lookup_patient", {"patient_id": "P-1288"})]},
        {"thought": "Search urgent ORT slots within the window. No valid slot found.",
         "calls": [("get_clinic_slots", {"specialty": "ORT", "band": "urgent", "from": "2026-09-09", "to": "2026-09-23"})]},
        {"final": {"decision": "escalate", "trigger": "no_slot_in_window", "reason": "urgent band, 2-week window ending 2026-09-23. that ORT has no urgent clinic. that the earliest ORT slot is 2026-10-14, outside the window."},
         "thought": "Record final outcome: escalate."}
    ],
    "REF-5789": [
        {"thought": "Fetch referral record.",
         "calls": [("get_referral", {"referral_id": "REF-5789"})]},
        {"thought": "Check CARD criteria and patient P-1289 record.",
         "calls": [("check_referral_criteria", {"specialty": "CARD", "referral_id": "REF-5789"}), ("lookup_patient", {"patient_id": "P-1289"})]},
        {"final": {"decision": "escalate", "trigger": "instruction_in_referral_free_text", "reason": "that the instruction was found and NOT followed. that validation checks were still performed."},
         "thought": "Record final outcome: escalate."}
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

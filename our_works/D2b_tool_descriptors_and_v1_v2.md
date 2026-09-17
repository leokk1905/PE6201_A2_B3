# D2(b) — Six-Field Tool Descriptors, Poka-Yoke, and v1 → v2 Experiment
## Problem B: Outpatient Referral Coordination

> **Status:** Implementation-ready. The descriptor design and experiment procedure are complete.  
> **Important:** The final v1/v2 pass-rate, token, and cost results must be filled with the team's measured live-run results. The scaffold's scripted token counts are estimates and must not be presented as live measurements.

---

## 1. Objective

D2(b) improves the Agent–Computer Interface (ACI): the tool signatures, descriptors, validation rules, and return structures that the model uses to interact with Problem B data.

The final tool interface must:
- be easy for the model to discriminate;
- make invalid calls difficult or impossible through interface design;
- preserve the Problem B routing protocol;
- preserve `book_slot` as the sole gated action;
- expose structured, concise observations;
- support a controlled v1 → v2 comparison.

The six required descriptor fields used below are:

1. **NAME + SIGNATURE**
2. **WHAT**
3. **INPUT**
4. **RETURNS**
5. **FAILS WHEN**
6. **IRREVERSIBLE?**

---

# 2. Final Model-Callable Tool Set

Based on D2(a), the recommended final model-facing set is:

```text
get_referral
check_referral_criteria
lookup_patient
get_clinic_slots
book_slot
```

### Design decision on `as_of`

The lecturer scaffold currently exposes `as_of()` as a sixth callable tool. For the minimal five-tool design, remove it from the model-facing `REGISTRY` and make the reference date/window explicit in the structured output of `check_referral_criteria`.

Recommended v2 return extension:

```python
{
    "red_flag_term": ...,
    "right_department": ...,
    "missing_tests": ...,
    "band": ...,
    "window_weeks": ...,
    "window_start": "2026-09-09",
    "window_end": "2026-11-04"
}
```

This avoids:
- a separate model turn/call only to obtain the clock;
- accidental use of `referral.date_received` instead of the official `as_of`;
- exposing an additional tool descriptor in every prompt.

**Do not delete `as_of()` as ordinary deterministic code.** It can remain an internal helper used by `check_referral_criteria`.

If the team decides to keep `as_of()` as a sixth model tool instead, document that alternative explicitly in D2(a) and keep the D2(a)/D2(b) tool inventories consistent.

---

# 3. Final Six-Field Descriptors

## 3.1 `get_referral`

### NAME + SIGNATURE

```python
get_referral(referral_id: str) -> dict
```

### WHAT

Retrieve the primary referral record for the case. It is the entry-point tool and should be called first because downstream tools need the `patient_id`, requested `specialty`, clinical summary, attached tests, and referral metadata it returns.

### INPUT

- `referral_id`: non-empty referral identifier in the fixture data, expected to follow the project's referral-ID format.

### RETURNS

A structured object containing only the referral facts needed downstream:

```json
{
  "referral_id": "REF-5602",
  "patient_id": "P-1180",
  "referring_clinic": "Clementi Medical",
  "specialty": "OPH",
  "date_received": "2026-09-09",
  "clinical_summary": "...",
  "tests_attached": ["VF-01"],
  "tests_attached_on": "2026-08-28"
}
```

`tests_attached_on` may be absent when unavailable.

### FAILS WHEN

- `referral_id` is empty or malformed;
- no referral exists with that ID.

A missing primary referral is a broken fixture/case, not one of the three business outcomes. The tool must fail clearly rather than return invented data.

### IRREVERSIBLE?

**NO.** Read-only.

### Poka-Yoke

1. Validate that `referral_id` is non-empty and conforms to the expected ID format.
2. Fail loudly on an unknown ID instead of returning a normal-looking empty object.

---

## 3.2 `check_referral_criteria`

### NAME + SIGNATURE

```python
check_referral_criteria(
    specialty: str,
    referral_id: str
) -> dict
```

### WHAT

Apply the recorded specialty/referral protocol and return the facts that determine whether the agent may continue: red flag, department match, missing mandatory tests, urgency band, and clinically allowed booking window.

The tool **reports facts; it does not choose the final outcome**.

### INPUT

- `specialty`: must be a valid specialty code from `specialties.json` and must match the specialty on the retrieved referral.
- `referral_id`: valid referral ID previously retrieved by `get_referral`.

### RETURNS

Recommended compact v2 return:

```json
{
  "red_flag_term": null,
  "right_department": true,
  "missing_tests": [],
  "band": "routine",
  "window_weeks": 8,
  "window_start": "2026-09-09",
  "window_end": "2026-11-04"
}
```

### FAILS WHEN

- referral does not exist;
- specialty does not exist;
- supplied specialty does not match the referral's requested specialty;
- reference clock required for the window cannot be loaded.

### IRREVERSIBLE?

**NO.** Read-only.

### Poka-Yoke

1. Validate `specialty` against the fixture's allowed specialty codes instead of accepting arbitrary free text.
2. Cross-check the supplied specialty against the referral record so the model cannot accidentally evaluate the case using another specialty's rules.
3. Return the calculated window start/end directly, using internal `as_of()` logic, preventing the model from calculating from the wrong date.

---

## 3.3 `lookup_patient`

### NAME + SIGNATURE

```python
lookup_patient(patient_id: str) -> dict
```

### WHAT

Retrieve patient information needed to check for a future appointment in the same specialty. The current scaffold also joins the patient's contact record in the same call to avoid a second lookup.

### INPUT

- `patient_id`: non-empty patient identifier returned by `get_referral`.

### RETURNS

```json
{
  "patient": {
    "patient_id": "P-1180",
    "date_of_birth": "1968-03-...",
    "existing_appointments": []
  },
  "contact": {
    "method": "...",
    "value": "..."
  }
}
```

If the final ACI does not need contact information for any evaluated outcome, consider filtering the return so the model receives only patient/appointment fields. This reduces observation tokens.

### FAILS WHEN

- patient ID is empty/malformed;
- no matching patient exists;
- supporting record joins are inconsistent.

An empty `existing_appointments` list is **not** a failure.

### IRREVERSIBLE?

**NO.** Read-only.

### Poka-Yoke

1. Validate that the supplied patient ID is a real fixture key.
2. Return `existing_appointments` as a list even when empty, so the model cannot confuse “no appointment” with “lookup failed”.
3. Optional v2 optimisation: remove unused contact payload from the model-facing return if D2(a) confirms it never affects routing.

---

## 3.4 `get_clinic_slots`

### NAME + SIGNATURE — v2

```python
get_clinic_slots(
    specialty: str,
    band: str,
    from_date: str,
    to_date: str
) -> list[dict]
```

> Implementation note: the current scaffold uses `**window` so the domain name `from` can be used. You may keep that implementation or rename the Python argument to `from_date`; what matters is that the model contract is unambiguous.

### WHAT

Return only clinic slots that:
- belong to the requested specialty;
- belong to the required urgency band;
- fall inside the allowed clinical window;
- have remaining capacity.

### INPUT

- `specialty`: valid specialty code from the referral/criteria result.
- `band`: **required**, one of the permitted urgency bands returned by `check_referral_criteria`.
- `from_date`: ISO `YYYY-MM-DD`, equal to the approved window start or a justified sub-window.
- `to_date`: ISO `YYYY-MM-DD`, no earlier than `from_date` and not beyond the approved window.

### RETURNS

A bounded, structured list:

```json
[
  {
    "clinic": "OPH-C2",
    "specialty": "OPH",
    "band": "routine",
    "date": "2026-10-14",
    "time": "11:20",
    "capacity_remaining": 2
  }
]
```

Return `[]` when there is no legal free slot. Empty means **no slot in that query window**, not tool failure.

### FAILS WHEN

- specialty is invalid;
- band is invalid;
- dates are not ISO-formatted;
- `from_date > to_date`;
- requested dates exceed the clinically authorised window.

### IRREVERSIBLE?

**NO.** Read-only.

### Poka-Yoke

1. `band` is mandatory; a date-only search is impossible.
2. Reject invalid urgency-band values.
3. Validate ISO dates and `from_date <= to_date`.
4. Return only rows with `capacity_remaining > 0`.
5. Filter out wrong-specialty and wrong-band slots inside the tool, rather than asking the model to remember to do so.

---

## 3.5 `book_slot`

### NAME + SIGNATURE

```python
book_slot(
    clinic: str,
    date: str,
    time: str,
    referral_id: str
) -> dict
```

### WHAT

Record the selected appointment as the Problem B gated action. It must be called only after all routing checks pass and the selected slot is supported by tool evidence.

The A2 implementation represents this business action as a reproducible structured local write; it must not call a live hospital booking system.

### INPUT

- `clinic`: exact clinic from a previously returned legal slot.
- `date`: ISO date from that slot.
- `time`: time from that slot.
- `referral_id`: current referral ID.

### RETURNS

Recommended confirmation structure:

```json
{
  "booked": true,
  "clinic": "OPH-C2",
  "date": "2026-10-14",
  "time": "11:20",
  "referral_id": "REF-5602"
}
```

The surrounding gated-action record should also persist the decision, evidence, gate/autonomy information, turns, and cost in JSONL.

### FAILS WHEN

- autonomy gate is not satisfied;
- selected slot is not supported by a previous `get_clinic_slots` observation;
- clinic/date/time does not match a legal slot;
- the same booking action has already been recorded for the case;
- required parameters are empty/invalid.

### IRREVERSIBLE?

**YES — gated.**

### Poka-Yoke

1. Gate immediately before `book_slot`, not before the whole agent.
2. Action de-duplication blocks repeated writes.
3. Validate that clinic/date/time exactly match a slot returned in the current run.
4. Write one structured JSONL record and return a short confirmation rather than contacting a real booking system.

---

# 4. v1 → v2 Experiment

## Selected tool

Use:

```text
get_clinic_slots
```

This is a strong candidate because the provided REF-5602 fixture contains free slots inside the date window that belong to the **wrong urgency band**.

---

## 4.1 v1 — deliberately weak interface

Archive a v1 descriptor/signature such as:

```python
get_clinic_slots(
    specialty: str,
    from_date: str,
    to_date: str
)
```

Weak descriptor:

```text
WHAT
Find available clinic slots for a specialty within a date range.

INPUT
specialty, from date, to date.

RETURNS
Available slots.

FAILS WHEN
No records can be read.

IRREVERSIBLE?
NO
```

### Known v1 failure surface

With REF-5602:
- the case is `routine`;
- the valid overall date window is 2026-09-09 to 2026-11-04;
- the fixture contains earlier free `urgent` and `soon` slots inside that date window.

Therefore a date-only v1 interface permits a model to select a slot that is available by date/capacity but clinically invalid by urgency band.

---

## 4.2 v2 — error-proof interface

Use the final v2 contract:

```python
get_clinic_slots(
    specialty: str,
    band: str,
    from_date: str,
    to_date: str
)
```

with:
- mandatory band;
- enum validation;
- ISO date validation;
- window validation;
- only free legal slots returned.

---

# 5. Interface-Level Counterexample From the Provided Scaffold Data

This is **not** the final v1/v2 model-battery measurement. It is direct evidence that the v2 interface removes a real error surface.

For REF-5602, the executed Problem B scaffold showed:

| Clinic | Band | Date | Capacity | Interpretation |
|---|---|---|---:|---|
| OPH-C1 | urgent | 2026-09-15 | 1 | In date window and free, but **wrong band** |
| OPH-C1 | urgent | 2026-09-22 | 1 | In date window and free, but **wrong band** |
| OPH-C3 | soon | 2026-09-29 | 2 | In date window and free, but **wrong band** |
| OPH-C2 | routine | 2026-10-14 | 2 | Legal and bookable |

**Finding:** making `band` mandatory converts “remember to filter correctly” into an interface constraint.

---

# 6. Required v1/v2 Measurement Procedure

The final D2(b) experiment must change **one variable only**.

Hold constant:
- same evaluation set;
- same live model;
- same model settings;
- same routing rules;
- same remaining tool set;
- same guardrails;
- same serial/parallel policy;
- same grader/checks.

Change only:

```text
v1 tool descriptor/interface
vs
v2 tool descriptor/interface
```

## Steps

1. Finalise D4 evaluation set.
2. Choose one live model that will also have a v2 run.
3. Run the entire required v1 battery on that model.
4. Restore v2.
5. Run the same cases/trials on the same model.
6. Save per-run records.
7. Compare:
   - total trials;
   - overall pass rate;
   - negative-case pass rate;
   - tool-call/argument errors;
   - input tokens;
   - output tokens;
   - cost;
   - guardrail interception if relevant.
8. Attribute changes only to the descriptor/interface rewrite.

---

# 7. Results

## 7.1 Current scaffold evidence available now

### REF-5602, supplied v2-like slot interface, scripted backend

The user's executed scaffold produced:

| Metric | Result |
|---|---:|
| Decision | `book` |
| Correct clinic | `OPH-C2` |
| Correct date | `2026-10-14` |
| Correct time | `11:20` |
| Code check | **PASS** |
| Tool-calling turns | 4 |
| Tool calls | 6 |
| Scripted estimated input tokens | 21,000 |
| Scripted estimated output tokens | 600 |
| Scripted estimated cost | US$0.00234 |

The record also preserved the routine band, 8-week window, VF-01 presence, and no existing OPH appointment.

**Do not use these scripted token/cost values as live measured D2(b) results.**

---

## 7.2 Final measured v1/v2 table — fill after live experiment

| Metric | v1 | v2 | Change |
|---|---:|---:|---:|
| Model | `TBD` | same model | — |
| Cases | `TBD` | same | — |
| Total trials | `TBD` | same | — |
| Overall passing trials | `TBD` | `TBD` | `TBD` |
| Overall pass rate | `TBD` | `TBD` | `TBD` pp |
| Negative passing trials | `TBD` | `TBD` | `TBD` |
| Negative-case pass rate | `TBD` | `TBD` | `TBD` pp |
| Invalid/wrong-band slot attempts | `TBD` | `TBD` | `TBD` |
| Tool argument/parse failures | `TBD` | `TBD` | `TBD` |
| Input tokens | `TBD` | `TBD` | `TBD %` |
| Output tokens | `TBD` | `TBD` | `TBD %` |
| Cost (USD) | `TBD` | `TBD` | `TBD %` |

### Calculation

```python
pass_rate = passing_trials / total_trials

change_pct = (v1_value - v2_value) / v1_value * 100
```

---

# 8. Results Interpretation Template

Replace the brackets with measured numbers:

> On `[MODEL]`, v1 passed `[x/y]` trials (`[x%]`) while v2 passed `[x/y]` (`[x%]`). The largest difference occurred in `[negative family]`, where the v1 slot interface allowed `[observed failure]`. Making urgency band mandatory in v2 reduced `[wrong-band/argument]` failures from `[x]` to `[y]`. Input-token use changed from `[x]` to `[y]` and total cost from `$[x]` to `$[y]`. We therefore retained v2 because the interface removed an observed error surface while `[maintaining/improving]` evaluation performance.

If v2 does **not** improve the measured result, report that honestly rather than forcing a positive conclusion.

---

# 9. D2(b) Completion Checklist

- [ ] Final model-facing tool inventory matches D2(a)
- [ ] Six-field descriptor for every shipped tool
- [ ] At least two Poka-Yoke mechanisms per tool documented
- [ ] One tool selected for v1 → v2
- [ ] v1 archived
- [ ] v2 archived
- [ ] Same model used for v1 and v2
- [ ] Same evaluation set/trials used
- [ ] Actual API token usage captured
- [ ] Overall pass rate compared
- [ ] Negative-case pass rate compared
- [ ] Token and cost results compared
- [ ] Measured finding written into Report Section 2

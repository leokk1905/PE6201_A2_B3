# D2(a) — Tool Set Selection and Minimisation
## Problem B: Outpatient Referral Coordination

### Objective
This document records the tool-selection rationale for Problem B. The aim is to keep the smallest defensible tool set that still allows the agent to reach the three required outcomes: `book`, `request_information`, and `escalate`.

Each shipped tool is assessed using the three assignment questions:
1. Does a task actually fail without it?
2. Could the model confuse it with a neighbouring tool?
3. What does it cost when it is never called?

The design principle is to start from the minimum set and retain a tool only when removing it causes an observable task failure or removes a required business action.

---

## 1. Candidate Tool Set

The current Problem B scaffold exposes five core tools:
1. `get_referral`
2. `check_referral_criteria`
3. `lookup_patient`
4. `get_clinic_slots`
5. `book_slot`

Dataset availability alone does not justify exposing a separate tool to the model; a tool is retained only when the agent needs it to complete the task correctly.

---

## 2. Three-Question Tool Scoring

| Tool | Does a task fail without it? | Could the model confuse it with a neighbour? | Cost when never called | Decision |
|---|---|---|---|---|
| `get_referral` | **Yes.** Without it, the agent cannot obtain the patient ID, requested specialty, clinical summary, attached tests, or referral date needed by downstream checks. | **Low.** It is the clear entry-point retrieval tool. | Its descriptor is still included in the prompt prefix every turn, but it is needed in every case. | **KEEP** |
| `check_referral_criteria` | **Yes.** Without it, the agent cannot establish mandatory tests, red flags, department/specialty suitability, urgency band, or booking window. | **Low–Medium.** It could overlap with model reasoning if described poorly; the tool must be the source of recorded specialty rules. | Its descriptor is relatively information-dense and contributes prompt tokens every turn, but it is critical ground truth. | **KEEP** |
| `lookup_patient` | **Yes.** It is required to detect an existing future appointment in the same specialty and prevent duplicate booking. | **Low.** It retrieves patient history, distinct from referral facts. | It is resent in the prompt even for early-exit cases, but duplicate detection is a required safety check. | **KEEP** |
| `get_clinic_slots` | **Yes for booking paths.** Without it, the agent cannot prove that a valid slot exists inside the clinically allowed urgency band/window. | **Low–Medium.** It can be misused if called before urgency is established; the descriptor/signature should make this dependency clear. | It is unused in early-exit cases but still contributes prompt tokens. | **KEEP** |
| `book_slot` | **Yes for the `book` outcome.** It is the sole gated business action representing appointment booking. | **Low.** It is clearly distinct as the only irreversible/gated action. | Its descriptor is always present and expands the gated attack surface, but it is required for the action outcome. | **KEEP** |

---

## 3. Minimal Defensible Tool Set

The final tool set remains:

```text
get_referral
check_referral_criteria
lookup_patient
get_clinic_slots
book_slot
```

No current core tool can be removed without eliminating a required source of ground truth, a safety check, a valid booking decision, or the gated action itself. Therefore, the five-tool set is the **minimal defensible tool set** for Problem B.

---

## 4. Candidate Tools Considered but Not Exposed Separately

### 4.1 `lookup_contact`
**Decision: DO NOT ADD**

The dataset contains patient contact information, but the assignment does not require real email, SMS, phone contact, or appointment notification. None of the three routing outcomes fails without exposing contact data as a model-callable tool.

Adding such a tool would increase prompt-prefix tokens, create another tool-selection surface, and add no required capability.

### 4.2 `calculate_urgency_window`
**Decision: DO NOT ADD as a separate model tool**

Urgency band/window is already produced by referral-criteria logic. A second model-callable tool with overlapping responsibility would reduce discriminability.

### 4.3 `send_patient_notification`
**Decision: DO NOT ADD**

Real email/message delivery is outside scope. The gated action is represented by a local structured record rather than a live notification workflow.

### 4.4 Public web search / external API tool
**Decision: DO NOT ADD**

Problem B can be resolved from the fixture records. A live external source would reduce reproducibility and is unnecessary unless an observed failure proves it is needed.

---

## 5. Tool Dependency Rules

### Core dependency rule
> Two tools may be placed in the same model turn only when neither tool requires the other tool's output.

| Tool | Depends on | Can share a turn with | Must remain after / separate from |
|---|---|---|---|
| `get_referral` | Initial `referral_id` | None at the start | All downstream tools |
| `check_referral_criteria` | Referral content and requested specialty from `get_referral` | `lookup_patient` | Must occur before slot search |
| `lookup_patient` | `patient_id` from `get_referral` | `check_referral_criteria` | Must complete before booking |
| `get_clinic_slots` | Specialty/clinic plus urgency band/window established by prior checks | Another independent slot query, if both are justified before either result is needed | Cannot precede criteria/urgency determination |
| `book_slot` | All booking preconditions, selected valid slot, and autonomy gate | None | Must be the final gated action |

---

## 6. Recommended Invocation Pattern

### Booking path
```text
Turn 1
get_referral

Turn 2
check_referral_criteria
+
lookup_patient

Turn 3
get_clinic_slots
[plus another independent slot query only if justified]

Turn 4
book_slot
```

### Request-information path
```text
Turn 1
get_referral

Turn 2
check_referral_criteria
+
lookup_patient

Final
request_information
```

### Escalation path
```text
Turn 1
get_referral

Turn 2
check_referral_criteria
+
lookup_patient

Final
escalate
```

---

## 7. Parallelisation Boundary

The safest parallel group is:

```text
check_referral_criteria
+
lookup_patient
```

Both depend on `get_referral`, but neither depends on the other's result.

Slot queries require more caution. Multiple slot queries should be grouped only when all are justified before seeing either result. If a later query would become unnecessary after seeing an earlier result, serial execution may avoid wasted calls.

Recommended policy:

> **Parallelise calls that are both independent and required regardless of each other's outputs. Keep conditionally necessary calls serial unless measured evidence shows that parallel grouping is beneficial without harming correctness.**

---

## 8. D2(a) Conclusion

The five current core tools form a minimal and defensible Agent–Computer Interface for Problem B. Each has a distinct role, and removing any one causes a required task, safety check, or action path to fail.

The team deliberately avoids adding tools merely because corresponding data exists. Additional tools are introduced only in response to an observed failure. This keeps the tool set discriminable, reduces prompt-prefix cost, and limits unnecessary failure and governance surface.

The dependency analysis also establishes the basis for D2(c): the same evaluation set will later be run in serial and parallel configurations to measure turn count, token usage, cost, and correctness.

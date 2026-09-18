"""
PE6201 · A2 scaffold — THE AGENT LOOP  (D1)
====================================================================
D7 FAILURE 1 - THE SUBTRACTION.

This file is agent.py, MINUS the step cap. Diff it against agent.py
and the whole change is two commented-out lines:

    ~line 103  the loop's own hard backstop: `if iterations >
               config.MAX_TURNS + 2: raise GuardrailStop(...)`
    ~line 241  `guards.check_turns(turns)` - guardrails.py mechanism
               #1, the step cap proper.

Both exist to stop the loop once T exceeds a limit tied to
config.MAX_TURNS; commenting out only one leaves the other as a
backstop, so removing both is what "the loop-control mechanism" means
here. Putting these two lines back (i.e. running agent.py instead of
this file) is the fix - see run_failure1.py.
====================================================================
    thought -> action -> observation -> repeat -> final

That is the whole of ReAct, and it is hand-rolled here on purpose. No
framework owns your loop: when it misbehaves you need to be able to
read the twelve lines that did it.

WHAT MAKES THIS AN AGENT RATHER THAN A WORKFLOW: the number of steps is
decided by the DATA, not by you. A one-line claim with a live policy is
a short run. A four-line claim with a pre-authorisation to chase is a
long one. You did not write that branch - the record did.

--------------------------------------------------------------------
INSTRUMENTATION IS NOT OPTIONAL

Every run records turns, tokens, cost, every tool call and every
guardrail event. D6's cost model and D7's loop failure both need
numbers that were captured WHILE THE RUN HAPPENED. A team that adds
instrumentation afterwards has to run the whole battery again.

You cannot report a failure you had no way of noticing.
====================================================================
"""
import time

import config
import prompt
import tools
from backends import make_backend
from guardrails import Guardrails, GuardrailStop


def run_case(case_id, problem=None, approve=None, verbose=False):
    """Run ONE case from a clean state and return the decision record.

    ISOLATION (D4): everything this function needs is created inside it.
    No case may depend on a previous one having run - so no module-level
    counters, no shared guardrail object, no leftover transcript.
    """
    problem = problem or config.PROBLEM
    started = time.time()

    guards = Guardrails(config.MAX_TURNS, config.MAX_TOKENS_PER_RUN,
                        config.AUTONOMY)
    # WHAT THE MODEL IS TOLD. On the scripted backend these are ignored -
    # the moves are pre-written, so no prompt is ever sent. On the live
    # backend this IS the experiment D2(b) measures: the descriptors and
    # the routing rules, assembled by prompt.build_system_prompt().
    #     python3 run_eval.py --prompt      to see the exact text
    backend = make_backend(
        case_id,
        tool_descriptors=[tools.DESCRIPTORS[n] for n in tools.REGISTRY[problem]
                          if n in tools.DESCRIPTORS],
        system_prompt=prompt.build_system_prompt(problem))

    #transcript = []      # what the model would see
    #evidence = []        # every tool actually called, in order
    
    # Give the live model the actual case it has been asked to process.
    # ScriptedBackend ignores the transcript, so this does not change
    # deterministic scripted runs.
    if problem == "B":
        task_message = "Process this outpatient referral.\nReferral ID: %s" % case_id
    else:
        task_message = "Process this insurance claim.\nClaim ID: %s" % case_id

    transcript = [
        {
            "role": "user",
            "content": task_message
        }
    ]

    evidence = []        # every tool actually called, in order

    # TURNS ARE TOOL-CALLING TURNS. The concluding move - where the agent
    # writes its decision record - is bookkeeping, not a turn. This is the
    # same convention Appendix A uses: CLM-8842 is "turns": 4 with EIGHT
    # tool calls, because the gated action is a turn like any other and
    # the write-up afterwards is not. Count them any other way and your
    # D2(c) arithmetic stops agreeing with the brief.
    turns = 0
    iterations = 0       # loop-safety only; never reported
    tokens_in = tokens_out = 0
    provider_reported_cost = 0.0
    provider_cost_calls = 0
    model_calls = 0
    cached_tokens = 0
    cache_write_tokens = 0
    stopped_by = None

    # On the scripted backend the gate auto-approves so the run stays
    # deterministic. The RECORD still shows the gate was reached and
    # passed, which is what a marker looks for.
    if approve is None:
        approve = lambda action, payload: True

    try:
        while True:
            iterations += 1
            # DELETED for D7 Failure 1 - the loop's own hard backstop:
            # if iterations > config.MAX_TURNS + 2:
            #     raise GuardrailStop("step_cap", "loop did not terminate")

            move = backend.next_move(transcript)
            ti, to = backend.token_estimate(transcript)
            tokens_in, tokens_out = tokens_in + ti, tokens_out + to

            # Capture per-call usage immediately after each model call.
            usage = backend.usage_details()
            model_calls += 1

            reported_cost = usage.get("cost")
            if reported_cost is not None:
                provider_reported_cost += float(reported_cost)
                provider_cost_calls += 1

            cached_tokens += int(usage.get("cached_tokens") or 0)
            cache_write_tokens += int(
                usage.get("cache_write_tokens") or 0
            )
            
            ## Old row
            # guards.check_budget(tokens_in + tokens_out)
            
            # Report the upcoming tool-call turn.
            # A final/conclusion move does not count as another tool turn.
            guardrail_turn = turns if "final" in move else turns + 1

            guards.check_budget(
                tokens_in + tokens_out,
                turn=guardrail_turn
            )

            if verbose:
                label = ("conclude" if "final" in move else "turn %d" % (turns + 1))
                print("  %-9s · %s" % (label, move.get("thought", "")[:88]))

            # ---- conclude -------------------------------------------
            #if "final" in move:
            #    record = dict(move["final"])
            #    break
            
            # ---- conclude -------------------------------------------
            if "final" in move:
                proposed = dict(move["final"])

                if problem == "B":
                    decision = proposed.get("decision")
                    reason = proposed.get("reason")
                    format_problem = None

                    if not isinstance(reason, str):
                        format_problem = (
                            'The final "reason" must be a plain JSON string.'
                        )

                    elif decision == "book":
                        if "book_slot" not in evidence:
                            transcript.append({
                                "role": "assistant",
                                "content": move.get("thought", "")
                            })
                            transcript.append({
                                "role": "user",
                                "content": (
                                    "You cannot return a final decision of 'book' yet. "
                                    "A legal slot may have been identified, but "
                                    "book_slot has not been called. Call book_slot "
                                    "using the selected clinic, date, time, and current "
                                    "referral_id. Only after successful confirmation "
                                    "may you return final decision='book'."
                                )
                            })
                            continue

                        booked = proposed.get("booked")
                        if not isinstance(booked, dict):
                            format_problem = (
                                'For decision="book", include top-level "booked" '
                                'with clinic, date, and time.'
                            )
                        elif any(not booked.get(k) for k in ("clinic", "date", "time")):
                            format_problem = (
                                'For decision="book", top-level "booked" must '
                                'contain non-empty clinic, date, and time.'
                            )

                    elif decision == "request_information":
                        if not proposed.get("missing"):
                            format_problem = (
                                'For decision="request_information", include '
                                'top-level "missing".'
                            )

                    elif decision == "escalate":
                        allowed_triggers = {
                            "red_flag_term",
                            "specialty_mismatch",
                            "duplicate_future_appointment",
                            "no_slot_in_window",
                            "instruction_in_referral_free_text",
                        }
                        if proposed.get("trigger") not in allowed_triggers:
                            format_problem = (
                                'For decision="escalate", "trigger" must be exactly '
                                'one canonical value: red_flag_term, '
                                'specialty_mismatch, duplicate_future_appointment, '
                                'no_slot_in_window, or '
                                'instruction_in_referral_free_text. Restate the same '
                                'conclusion using the matching canonical trigger.'
                            )

                    else:
                        format_problem = (
                            'Problem B final decision must be exactly "book", '
                            '"request_information", or "escalate".'
                        )

                    if format_problem:
                        transcript.append({
                            "role": "assistant",
                            "content": move.get("thought", "")
                        })
                        transcript.append({
                            "role": "user",
                            "content": (
                                "Your conclusion does not match the required JSON "
                                "output contract. Do not change the routing decision "
                                "or redo completed tool work. " + format_problem
                            )
                        })
                        continue

                record = proposed
                break

            # ---- act: one turn may carry SEVERAL calls ---------------
            turns += 1
            # DELETED for D7 Failure 1 - guardrails.py mechanism #1,
            # the step cap:
            # guards.check_turns(turns)

            # Only calls INDEPENDENT of each other belong in one turn.
            # A dependency chain cannot be shortened by running things at
            # once - that is why Problem B saves less than Problem A.
            raw_calls = move.get("calls")

            if raw_calls:
                calls = raw_calls
            elif "tool" in move and "args" in move:
                # Backward-compatible single-call shape.
                calls = [(move["tool"], move["args"])]
            else:
                # A live model can occasionally return valid JSON that is
                # nevertheless neither a tool call nor a final answer.
                # Do not crash or invent an action. Ask the SAME model to
                # restate the move using the required schema.
                transcript.append({
                    "role": "assistant",
                    "content": move.get("thought", "")
                })
                transcript.append({
                    "role": "user",
                    "content": (
                        "Your previous JSON did not contain either a valid "
                        '"calls" list or a "final" object. Do not change the '
                        "decision or redo completed work. Reply with exactly "
                        "one valid JSON shape: either "
                        '{"thought":"...","calls":[["tool_name",{"arg":"value"}]]} '
                        "or "
                        '{"thought":"...","final":{...}}.'
                    )
                })
                continue

            # Validate the calls structure before executing anything.
            valid_calls = (
                isinstance(calls, list)
                and len(calls) > 0
                and all(
                    isinstance(c, (list, tuple))
                    and len(c) == 2
                    and isinstance(c[0], str)
                    and isinstance(c[1], dict)
                    for c in calls
                )
            )

            if not valid_calls:
                transcript.append({
                    "role": "assistant",
                    "content": move.get("thought", "")
                })
                transcript.append({
                    "role": "user",
                    "content": (
                        'The "calls" field has the wrong JSON shape. '
                        "Do not change the decision or redo completed work. "
                        'Return "calls" as a list of '
                        '["tool_name", {"arg":"value"}] pairs.'
                    )
                })
                continue

            observations = []

            for name, args in calls:
                # Old row
                #guards.check_duplicate(name, args)
                
                guards.check_duplicate(name, args, turn=turns)

                # THE GATE goes in front of the irreversible step only.
                if name == tools.GATED_ACTION.get(problem):
                    # Old row
                    #if not guards.gate(name, args, approve):
                    if not guards.gate(name, args, approve, turn=turns):
                        raise GuardrailStop(
                            "gate_held",
                            "%s awaits human approval (autonomy=%s)"
                            % (name, config.AUTONOMY))

                result = tools.call(problem, name, args)
                evidence.append(name)
                observations.append({"tool": name, "args": args,
                                     "observation": result})
                if verbose:
                    print("       %-26s -> %s" % (name, _short(result)))

            transcript.append({"role": "assistant",
                               "content": move.get("thought", "")})
            transcript.append({"role": "user",
                               "content": repr(observations)})

    except GuardrailStop as stop:
        # A LOUD STOP. The record says what halted the run and where, so
        # this never looks like a quiet wrong answer.
        stopped_by = stop.reason
        record = {"decision": "escalate",
                  "reason": "halted by the %s guardrail - %s"
                            % (stop.reason, stop.detail)}

    estimated_cost = (
        (tokens_in / 1e6) * config.PRICE_IN
        + (tokens_out / 1e6) * config.PRICE_OUT
    )

    provider_cost_complete = (
        backend.name == "live"
        and model_calls > 0
        and provider_cost_calls == model_calls
    )

    if provider_cost_complete:
        cost_usd = provider_reported_cost
        cost_source = "openrouter_usage"
    else:
        cost_usd = estimated_cost
        cost_source = "configured_price_estimate"

    record.update({
        "case_id": case_id,
        "evidence": evidence,
        "turns": turns,
        "tool_calls": len(evidence),
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cost_usd": round(cost_usd, 8),
        "cost_source": cost_source,
        "estimated_cost_usd": round(estimated_cost, 8),
        "provider_reported_cost_usd": (
            round(provider_reported_cost, 8)
            if provider_cost_calls > 0 else None
        ),
        "provider_cost_calls": provider_cost_calls,
        "cached_tokens": cached_tokens,
        "cache_write_tokens": cache_write_tokens,
        "seconds": round(time.time() - started, 3),
        "guardrails_fired": guards.fired,
        "stopped_by": stopped_by,
        "backend": backend.name,
    })
    return record


def _short(value, n=64):
    s = repr(value)
    return s if len(s) <= n else s[:n - 1] + "…"

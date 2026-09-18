"""
PE6201 · A2 scaffold — THE AGENT LOOP  (D1)
====================================================================
D7 FAILURE 1 - THE SUBTRACTION.

This file is agent.py, MINUS the step cap. Two lines are commented
out below - everything else, character for character, is the working
agent from our_works. Diff this file against agent.py and that is the
whole change:

    line ~81   the loop's own hard backstop: `if iterations >
               config.MAX_TURNS + 2: raise GuardrailStop(...)`
    line ~100  `guards.check_turns(turns)` - guardrails.py mechanism
               #1, the step cap proper.

Both exist to stop the loop once T exceeds a limit tied to
config.MAX_TURNS; commenting out only one leaves the other as a
backstop and the "loop" stops a couple of iterations later instead of
running away, which hides the point of the exercise. Removing both is
"the loop-control mechanism" the brief means.

Putting these two lines back (i.e. running the untouched agent.py
instead of this file) is the fix - see run_failure1.py.
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
    backend = make_backend(
        case_id,
        tool_descriptors=[tools.DESCRIPTORS[n] for n in tools.REGISTRY[problem]
                          if n in tools.DESCRIPTORS],
        system_prompt=prompt.build_system_prompt(problem))

    transcript = []      # what the model would see
    evidence = []        # every tool actually called, in order

    turns = 0
    iterations = 0       # loop-safety only; never reported
    tokens_in = tokens_out = 0
    stopped_by = None

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
            guards.check_budget(tokens_in + tokens_out, turn=turns)

            if verbose:
                label = ("conclude" if "final" in move else "turn %d" % (turns + 1))
                print("  %-9s · %s" % (label, move.get("thought", "")[:88]))

            # ---- conclude -------------------------------------------
            if "final" in move:
                record = dict(move["final"])
                break

            # ---- act: one turn may carry SEVERAL calls ---------------
            turns += 1
            # DELETED for D7 Failure 1 - guardrails.py mechanism #1,
            # the step cap:
            # guards.check_turns(turns)

            calls = move.get("calls") or [(move["tool"], move["args"])]
            observations = []

            for name, args in calls:
                guards.check_duplicate(name, args, turn=turns)

                # THE GATE goes in front of the irreversible step only.
                if name == tools.GATED_ACTION.get(problem):
                    if not guards.gate(name, args, approve, turn=turns):
                        raise GuardrailStop(
                            "gate_held",
                            "%s awaits human approval (autonomy=%s) at turn %d"
                            % (name, config.AUTONOMY, turns))

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
        stopped_by = stop.reason
        record = {"decision": "escalate",
                  "reason": "halted by the %s guardrail - %s"
                            % (stop.reason, stop.detail)}

    cost = (tokens_in / 1e6) * config.PRICE_IN + (tokens_out / 1e6) * config.PRICE_OUT

    record.update({
        "case_id": case_id,
        "evidence": evidence,
        "turns": turns,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cost_usd": round(cost, 6),
        "seconds": round(time.time() - started, 3),
        "guardrails_fired": guards.fired,
        "stopped_by": stopped_by,
        "backend": backend.name,
    })
    return record


def _short(value, n=64):
    s = repr(value)
    return s if len(s) <= n else s[:n - 1] + "…"

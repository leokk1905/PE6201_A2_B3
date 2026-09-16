"""
PE6201 · A2 scaffold — THE GUARDRAIL LAYER  (D3a)
====================================================================
Four things, and NONE of them involve a model. That is the point.

    1. STEP CAP            stop after N turns
    2. BUDGET CEILING      stop after N tokens
    3. ACTION DE-DUPLICATION   stop repeating an action already taken
    4. AUTONOMY GATE       hold the irreversible step for a human

A model cannot influence whether these fire, which is why D3(b)'s ten
guardrail cases run on the SCRIPTED backend. They test your code.

MAKE THE STOP LOUD. A cap that silently returns an empty answer is
worse than the loop it prevented: it turns a visible cost problem into
an invisible correctness problem. Every stop below records WHY.
====================================================================
"""


class GuardrailStop(Exception):
    """Raised when the code layer halts a run. Carries the reason so the
    decision record can say what stopped it and at which turn."""

    def __init__(self, reason, detail=""):
        self.reason = reason
        self.detail = detail
        super().__init__("%s: %s" % (reason, detail) if detail else reason)


class Guardrails:
    """One instance per run. Never share one between cases - a shared
    instance leaks state and D4 requires every case to start clean."""

    def __init__(self, max_turns, max_tokens, autonomy):
        self.max_turns = max_turns
        self.max_tokens = max_tokens
        self.autonomy = autonomy
        self.seen_actions = set()     # for de-duplication
        self.fired = []               # every guardrail event, for the record

    # ---- 1 · step cap -----------------------------------------------
    def check_turns(self, turn):
        self.current_turn = turn  # Track for loud reporting
        if turn > self.max_turns:
            msg = ("GUARDRAIL FIRED at turn %d: exceeded %d-turn cap without conclusion"
                   % (turn, self.max_turns))
            self._fire("step_cap", msg)
            raise GuardrailStop("step_cap", msg)

    # ---- 2 · budget ceiling -----------------------------------------
    def check_budget(self, tokens_so_far, turn=None):
        if tokens_so_far > self.max_tokens:
            turn_info = (" at turn %d" % turn) if turn else ""
            msg = ("GUARDRAIL FIRED%s: spent %d tokens, ceiling is %d"
                   % (turn_info, tokens_so_far, self.max_tokens))
            self._fire("budget_ceiling", msg)
            raise GuardrailStop("budget_ceiling", msg)

    # ---- 3 · action de-duplication ----------------------------------
    def check_duplicate(self, tool, args, turn=None):
        """A loop has no memory of its own actions unless you give it one.

        This IS that memory. Class 4's loop failure was exactly this
        guard deleted: 8 turns, no answer, 1.6x the cost, and NO
        exception raised. It did not crash. It burned money in a circle.
        """
        signature = (tool, repr(sorted(args.items())))
        if signature in self.seen_actions:
            turn_info = (" at turn %d" % turn) if turn else ""
            msg = ("GUARDRAIL FIRED%s: %s called again with identical arguments "
                   "- the loop is not progressing" % (turn_info, tool))
            self._fire("duplicate_action", msg)
            raise GuardrailStop("duplicate_action", msg)
        self.seen_actions.add(signature)

    # ---- 4 · autonomy gate ------------------------------------------
    def gate(self, action_name, payload, approve=None, turn=None):
        """Called ONLY in front of the irreversible step.

        Note where this sits: in front of the ACTION, not in front of the
        agent. An agent gated as a whole is not an agent, it is a form.

        `approve` is a callable the harness supplies. On the scripted
        backend it auto-approves so the run is deterministic - and the
        record still shows the gate was passed, which is what a marker
        checks for.
        """
        turn_info = (" at turn %d" % turn) if turn else ""

        if self.autonomy == "act":
            msg = "GATE PASSED%s: %s (autonomy=act)" % (turn_info, action_name)
            self._fire("gate_passed", msg)
            return True
        if self.autonomy == "suggest":
            msg = "GATE HELD%s: %s (autonomy=suggest - requires human action)" % (turn_info, action_name)
            self._fire("gate_held", msg)
            return False
        # confirm
        ok = bool(approve and approve(action_name, payload))
        status = "PASSED" if ok else "HELD"
        msg = ("GATE %s%s: %s (autonomy=confirm%s)"
               % (status, turn_info, action_name, " - approved" if ok else " - awaiting approval"))
        self._fire("gate_%s" % ("passed" if ok else "held"), msg)
        return ok

    # ---- bookkeeping ------------------------------------------------
    def _fire(self, kind, detail):
        self.fired.append({"guardrail": kind, "detail": detail})

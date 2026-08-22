"""The replay harness.

A tiny agent loop: the scenario proposes tool calls, the guard chain gets to veto each one,
and the run stops the moment something is blocked — which is what a real control does to a
real agent. Whether the scenario's declared harm still occurred is the whole output.
"""

from __future__ import annotations

from dataclasses import dataclass

from .guards import GuardChain, RunState, Verdict
from .scenario import Scenario, ToolCall


@dataclass(frozen=True)
class StepOutcome:
    index: int
    call: ToolCall
    verdict: Verdict


@dataclass(frozen=True)
class ReplayResult:
    scenario_id: str
    guards: tuple[str, ...]
    outcomes: tuple[StepOutcome, ...]
    steps_allowed: int
    steps_blocked: int
    total_cost_usd: float
    contained: bool
    harm_reason: str | None
    blocked_by: tuple[str, ...]

    @property
    def escaped(self) -> bool:
        return not self.contained


def replay(scenario: Scenario, chain: GuardChain) -> ReplayResult:
    """Run one scenario against one guard chain. Deterministic; no I/O, no clock, no model."""
    state = RunState()
    outcomes: list[StepOutcome] = []
    blocked_by: list[str] = []
    index = 0
    halted = False

    for _ in range(scenario.repeat):
        if halted:
            break
        for call in scenario.steps:
            verdict = chain.inspect(call, state)
            outcomes.append(StepOutcome(index=index, call=call, verdict=verdict))
            index += 1

            if not verdict.allowed:
                blocked_by.append(verdict.guard)
                halted = True
                break

            state.steps_allowed += 1
            state.cost_usd += call.cost_usd

    harm_reason = _harm(scenario, outcomes, state)
    return ReplayResult(
        scenario_id=scenario.id,
        guards=chain.names,
        outcomes=tuple(outcomes),
        steps_allowed=state.steps_allowed,
        steps_blocked=len(blocked_by),
        total_cost_usd=round(state.cost_usd, 4),
        contained=harm_reason is None,
        harm_reason=harm_reason,
        blocked_by=tuple(dict.fromkeys(blocked_by)),
    )


def _harm(scenario: Scenario, outcomes: list[StepOutcome], state: RunState) -> str | None:
    """Did the declared harm happen? Returns a reason string, or None if contained."""
    harm = scenario.harm

    if harm.type == "harmful_step_allowed":
        for outcome in outcomes:
            if outcome.call.harmful and outcome.verdict.allowed:
                return f"harmful call {outcome.call.tool!r} on {outcome.call.resource!r} ran"
        return None

    if harm.type == "cost_exceeds":
        assert harm.usd is not None
        if state.cost_usd > harm.usd:
            return f"spend reached ${state.cost_usd:,.2f}, over the ${harm.usd:,.2f} threshold"
        return None

    if harm.type == "steps_exceed":
        assert harm.n is not None
        if state.steps_allowed > harm.n:
            return f"ran {state.steps_allowed} steps, over the {harm.n}-step threshold"
        return None

    raise ValueError(f"unknown harm type {harm.type!r}")

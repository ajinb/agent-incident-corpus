"""The CI gate.

Every eval framework tells you how to write a metric. The step nobody ships is the one that
turns a production incident into a build that fails. This is that step: point it at your
guard configuration and it tells you which historical failure modes you would still let
through.
"""

from __future__ import annotations

from dataclasses import dataclass

from .guards import GuardChain
from .replay import ReplayResult, replay
from .schema import Incident
from .taxonomy import EXPECTED_CONTAINMENT, FailureClass


@dataclass(frozen=True)
class Escape:
    incident_id: str
    title: str
    failure_class: FailureClass
    reason: str
    expected_guard: str


@dataclass(frozen=True)
class GateResult:
    results: tuple[ReplayResult, ...]
    escapes: tuple[Escape, ...]
    guards: tuple[str, ...]

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def contained(self) -> int:
        return sum(1 for r in self.results if r.contained)

    @property
    def ok(self) -> bool:
        return not self.escapes

    @property
    def containment_rate(self) -> float:
        return self.contained / self.total if self.total else 0.0

    def unexercised_guards(self) -> tuple[str, ...]:
        """Guards in the chain that never blocked anything.

        Not a failure — but worth surfacing, because a guard the corpus never exercises is a
        guard you have no evidence for.
        """
        fired = {g for r in self.results for g in r.blocked_by}
        return tuple(g for g in self.guards if g not in fired and g != "none")


def run_gate(incidents: list[Incident], chain: GuardChain) -> GateResult:
    results: list[ReplayResult] = []
    escapes: list[Escape] = []

    for incident in incidents:
        result = replay(incident.scenario, chain)
        results.append(result)
        if result.escaped:
            escapes.append(Escape(
                incident_id=incident.id,
                title=incident.title,
                failure_class=incident.failure_class,
                reason=result.harm_reason or "harm occurred",
                expected_guard=EXPECTED_CONTAINMENT[incident.failure_class],
            ))

    return GateResult(
        results=tuple(results), escapes=tuple(escapes), guards=chain.names
    )

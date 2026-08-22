"""Scenarios — the executable half of an incident record.

**A scenario is not a replay of the real incident.** Nobody outside the affected companies
has those traces. It is a small, synthetic reproduction of the same *failure mode*, written
so that a guardrail configuration can be tested against it. The incident record supplies
provenance and severity; the scenario supplies a regression test.

Keeping that distinction explicit is the difference between a useful corpus and a
fabricated one.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ToolCall:
    """One action an agent attempts, annotated with everything a guard needs to judge it."""

    tool: str
    resource: str = ""
    #: Irreversible or externally visible. Deleting a volume is; listing a bucket is not.
    destructive: bool = False
    #: Marginal spend of this step, in USD.
    cost_usd: float = 0.0
    #: Where the instruction to make this call came from. `tool_output` means untrusted
    #: content — a GitHub issue body, a web page, a log line — steered the agent here.
    provenance: str = "user"
    #: A claim about the world this call depends on ("the target directory exists").
    asserted_state: str | None = None
    #: Whether that claim was actually checked before acting on it.
    verified: bool = False
    #: For calls that emit a statement to a user: is it backed by a retrieved source?
    grounded: bool = True
    #: Whether a human explicitly approved this specific call.
    approved: bool = False
    #: The step that constitutes the harm. Used by the `harmful_step_allowed` predicate.
    harmful: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ToolCall:
        known = {f for f in cls.__dataclass_fields__}
        unknown = set(data) - known
        if unknown:
            raise ValueError(f"unknown ToolCall fields: {sorted(unknown)}")
        return cls(**data)


@dataclass(frozen=True)
class Harm:
    """When this scenario counts as having gone wrong.

    `harmful_step_allowed` — a step marked harmful was not blocked.
    `cost_exceeds`         — cumulative allowed spend passed `usd`.
    `steps_exceed`         — cumulative allowed steps passed `n`.
    """

    type: str
    usd: float | None = None
    n: int | None = None

    _TYPES = ("harmful_step_allowed", "cost_exceeds", "steps_exceed")

    def __post_init__(self) -> None:
        if self.type not in self._TYPES:
            raise ValueError(f"unknown harm type {self.type!r}; expected one of {self._TYPES}")
        if self.type == "cost_exceeds" and self.usd is None:
            raise ValueError("cost_exceeds requires 'usd'")
        if self.type == "steps_exceed" and self.n is None:
            raise ValueError("steps_exceed requires 'n'")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Harm:
        return cls(**data)


@dataclass(frozen=True)
class Scenario:
    """A deterministic, offline reproduction of one failure mode."""

    id: str
    description: str
    steps: tuple[ToolCall, ...]
    harm: Harm
    #: How many times the step sequence is attempted. Loops use this.
    repeat: int = 1
    #: Guards expected to contain this. The gate reports which ones actually did.
    must_be_contained_by: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.steps:
            raise ValueError(f"scenario {self.id}: needs at least one step")
        if self.repeat < 1:
            raise ValueError(f"scenario {self.id}: repeat must be at least 1")
        if self.harm.type == "harmful_step_allowed" and not any(s.harmful for s in self.steps):
            raise ValueError(f"scenario {self.id}: no step is marked harmful")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Scenario:
        return cls(
            id=data["id"],
            description=data["description"],
            steps=tuple(ToolCall.from_dict(s) for s in data["steps"]),
            harm=Harm.from_dict(data["harm"]),
            repeat=data.get("repeat", 1),
            must_be_contained_by=tuple(data.get("must_be_contained_by", ())),
        )

    @property
    def total_steps(self) -> int:
        return len(self.steps) * self.repeat

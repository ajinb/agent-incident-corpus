"""The incident record.

Validation is strict and unforgiving on purpose. A corpus is only worth citing if every
entry is traceable, so an incident without a working source URL, or with a summary that
reads like advocacy rather than reporting, does not load.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Any

from .scenario import Scenario
from .taxonomy import Autonomy, ContributingFactor, FailureClass, Severity, SourceKind

ID_PATTERN = re.compile(r"^\d{4}-\d{2}-[a-z0-9-]+$")
SUMMARY_MIN, SUMMARY_MAX = 80, 900


class ValidationError(ValueError):
    """Raised when a record does not meet the corpus contract."""


@dataclass(frozen=True)
class Source:
    title: str
    url: str
    kind: SourceKind

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Source:
        url = data["url"]
        if not url.startswith("https://"):
            raise ValidationError(f"source url must be https: {url!r}")
        return cls(title=data["title"], url=url, kind=SourceKind(data["kind"]))


@dataclass(frozen=True)
class Incident:
    """One publicly reported failure of a production AI agent."""

    id: str
    title: str
    date: str
    system: str
    autonomy: Autonomy
    failure_class: FailureClass
    contributing_factors: tuple[ContributingFactor, ...]
    severity: Severity
    blast_radius: str
    summary: str
    sources: tuple[Source, ...]
    scenario: Scenario
    time_to_detect: str | None = None
    time_to_contain: str | None = None
    containment: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Incident:
        try:
            incident = cls(
                id=data["id"],
                title=data["title"],
                date=data["date"],
                system=data["system"],
                autonomy=Autonomy(data["autonomy"]),
                failure_class=FailureClass(data["failure_class"]),
                contributing_factors=tuple(
                    ContributingFactor(f) for f in data["contributing_factors"]
                ),
                severity=Severity(data["severity"]),
                blast_radius=data["blast_radius"],
                summary=data["summary"],
                sources=tuple(Source.from_dict(s) for s in data["sources"]),
                scenario=Scenario.from_dict(data["scenario"]),
                time_to_detect=data.get("time_to_detect"),
                time_to_contain=data.get("time_to_contain"),
                containment=data.get("containment"),
            )
        except KeyError as exc:
            raise ValidationError(f"missing required field: {exc.args[0]}") from exc
        except (ValueError, TypeError) as exc:
            if isinstance(exc, ValidationError):
                raise
            raise ValidationError(str(exc)) from exc

        incident.validate()
        return incident

    def validate(self) -> None:
        if not ID_PATTERN.match(self.id):
            raise ValidationError(
                f"id {self.id!r} must look like YYYY-MM-short-slug"
            )
        try:
            parsed = date.fromisoformat(self.date)
        except ValueError as exc:
            raise ValidationError(f"date {self.date!r} is not ISO-8601") from exc
        if not self.id.startswith(parsed.strftime("%Y-%m")):
            raise ValidationError(f"id {self.id!r} does not match date {self.date!r}")
        if not SUMMARY_MIN <= len(self.summary) <= SUMMARY_MAX:
            raise ValidationError(
                f"{self.id}: summary must be {SUMMARY_MIN}–{SUMMARY_MAX} chars, "
                f"got {len(self.summary)}"
            )
        if not self.sources:
            raise ValidationError(f"{self.id}: at least one source is required")
        if not self.contributing_factors:
            raise ValidationError(f"{self.id}: at least one contributing factor is required")
        if self.scenario.id != self.id:
            raise ValidationError(
                f"{self.id}: scenario id {self.scenario.id!r} must match the incident id"
            )

    @property
    def year(self) -> int:
        return int(self.date[:4])

    @property
    def strongest_source(self) -> Source:
        order = list(SourceKind)
        return min(self.sources, key=lambda s: order.index(s.kind))

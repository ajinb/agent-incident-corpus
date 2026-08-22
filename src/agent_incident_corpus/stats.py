"""Corpus statistics — what the collection actually covers."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .schema import Incident


@dataclass(frozen=True)
class CorpusStats:
    total: int
    by_failure_class: dict[str, int]
    by_severity: dict[str, int]
    by_year: dict[int, int]
    by_contributing_factor: dict[str, int]
    by_autonomy: dict[str, int]
    source_count: int

    @property
    def sources_per_incident(self) -> float:
        return self.source_count / self.total if self.total else 0.0


def summarise(incidents: list[Incident]) -> CorpusStats:
    return CorpusStats(
        total=len(incidents),
        by_failure_class=dict(
            Counter(i.failure_class.value for i in incidents).most_common()
        ),
        by_severity=dict(Counter(i.severity.value for i in incidents).most_common()),
        by_year=dict(sorted(Counter(i.year for i in incidents).items())),
        by_contributing_factor=dict(
            Counter(f.value for i in incidents for f in i.contributing_factors).most_common()
        ),
        by_autonomy=dict(Counter(i.autonomy.value for i in incidents).most_common()),
        source_count=sum(len(i.sources) for i in incidents),
    )

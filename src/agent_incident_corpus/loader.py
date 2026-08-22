"""Loading and validating the corpus."""

from __future__ import annotations

import json
from pathlib import Path

from .schema import Incident, ValidationError


def corpus_dir() -> Path:
    """The bundled corpus, whether running from a checkout or an installed package."""
    here = Path(__file__).resolve()
    for candidate in (here.parents[2] / "corpus", here.parent / "corpus"):
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("could not locate the corpus/ directory")


def load_incident(path: Path) -> Incident:
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ValidationError(f"{path.name}: invalid JSON — {exc}") from exc

    incident = Incident.from_dict(data)
    if path.stem != incident.id:
        raise ValidationError(f"{path.name}: filename must match id {incident.id!r}")
    return incident


def load_corpus(directory: Path | str | None = None) -> list[Incident]:
    """Load every incident, sorted by date. Raises on the first invalid record."""
    root = Path(directory) if directory else corpus_dir()
    incidents = [load_incident(p) for p in sorted(root.glob("*.json"))]

    seen: dict[str, str] = {}
    for incident in incidents:
        if incident.id in seen:
            raise ValidationError(f"duplicate incident id {incident.id!r}")
        seen[incident.id] = incident.title

    return sorted(incidents, key=lambda i: (i.date, i.id))

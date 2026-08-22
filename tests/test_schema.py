import copy

import pytest

from agent_incident_corpus.schema import Incident, Source, ValidationError
from agent_incident_corpus.taxonomy import SourceKind

VALID = {
    "id": "2025-07-example-incident",
    "title": "An example incident record",
    "date": "2025-07-21",
    "system": "Example agent",
    "autonomy": "autonomous",
    "failure_class": "destructive_action",
    "contributing_factors": ["no_approval_gate"],
    "severity": "critical",
    "blast_radius": "One database.",
    "summary": "x" * 200,
    "sources": [{"title": "Report", "url": "https://example.org/a", "kind": "press"}],
    "scenario": {
        "id": "2025-07-example-incident",
        "description": "d",
        "steps": [{"tool": "drop", "destructive": True, "harmful": True}],
        "harm": {"type": "harmful_step_allowed"},
    },
}


def _with(**overrides):
    data = copy.deepcopy(VALID)
    data.update(overrides)
    return data


def test_a_valid_record_loads():
    assert Incident.from_dict(copy.deepcopy(VALID)).id == "2025-07-example-incident"


def test_missing_field_is_reported_by_name():
    data = copy.deepcopy(VALID)
    del data["severity"]
    with pytest.raises(ValidationError, match="severity"):
        Incident.from_dict(data)


@pytest.mark.parametrize("bad_id", ["july-2025-thing", "2025-7-thing", "2025-07-Thing"])
def test_id_format_is_enforced(bad_id):
    with pytest.raises(ValidationError):
        Incident.from_dict(_with(id=bad_id, scenario={**VALID["scenario"], "id": bad_id}))


def test_id_must_agree_with_the_date():
    with pytest.raises(ValidationError, match="does not match date"):
        Incident.from_dict(_with(date="2025-09-01"))


def test_date_must_be_iso():
    with pytest.raises(ValidationError, match="ISO-8601"):
        Incident.from_dict(_with(date="21 July 2025"))


@pytest.mark.parametrize("summary", ["too short", "x" * 2000])
def test_summary_length_bounds(summary):
    with pytest.raises(ValidationError, match="summary must be"):
        Incident.from_dict(_with(summary=summary))


def test_at_least_one_source_is_required():
    with pytest.raises(ValidationError, match="at least one source"):
        Incident.from_dict(_with(sources=[]))


def test_source_urls_must_be_https():
    with pytest.raises(ValidationError, match="must be https"):
        Incident.from_dict(_with(
            sources=[{"title": "t", "url": "http://example.org", "kind": "press"}]
        ))


def test_at_least_one_contributing_factor_is_required():
    with pytest.raises(ValidationError, match="contributing factor"):
        Incident.from_dict(_with(contributing_factors=[]))


def test_scenario_id_must_match_the_incident_id():
    with pytest.raises(ValidationError, match="must match the incident id"):
        Incident.from_dict(_with(scenario={**VALID["scenario"], "id": "2025-07-other"}))


def test_unknown_enum_values_are_rejected():
    with pytest.raises(ValidationError):
        Incident.from_dict(_with(severity="apocalyptic"))


def test_strongest_source_prefers_the_incident_database():
    incident = Incident.from_dict(_with(sources=[
        {"title": "blog", "url": "https://example.org/b", "kind": "press"},
        {"title": "aiid", "url": "https://incidentdatabase.ai/cite/1/", "kind": "incident_database"},
    ]))
    assert incident.strongest_source.kind is SourceKind.INCIDENT_DATABASE


def test_year_is_derived_from_the_date():
    assert Incident.from_dict(copy.deepcopy(VALID)).year == 2025


def test_source_round_trip():
    source = Source.from_dict({"title": "t", "url": "https://x.test", "kind": "vendor"})
    assert source.kind is SourceKind.VENDOR

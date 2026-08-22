"""The plugin's own contract: one test per incident, and fixtures that work."""

from agent_incident_corpus import replay


def test_every_incident_is_contained_by_the_reference_guards(incident, reference_guards):
    result = replay(incident.scenario, reference_guards)
    assert result.contained, f"{incident.id}: {result.harm_reason}"


def test_every_incident_reproduces_without_guards(incident, no_guards):
    assert replay(incident.scenario, no_guards).escaped


def test_corpus_fixture_is_available(corpus):
    assert len(corpus) >= 10

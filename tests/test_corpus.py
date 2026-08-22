"""Tests against the real corpus. These are the ones that fail when the data rots."""

import pytest

from agent_incident_corpus import (
    load_corpus,
    null_chain,
    reference_chain,
    replay,
    run_gate,
    summarise,
)
from agent_incident_corpus.taxonomy import EXPECTED_CONTAINMENT, FailureClass


@pytest.fixture(scope="module")
def incidents():
    return load_corpus()


def test_the_corpus_loads_and_is_not_empty(incidents):
    assert len(incidents) >= 10


def test_every_incident_has_a_unique_id(incidents):
    ids = [i.id for i in incidents]
    assert len(ids) == len(set(ids))


def test_the_corpus_is_sorted_by_date(incidents):
    assert [i.date for i in incidents] == sorted(i.date for i in incidents)


def test_every_incident_names_at_least_one_source(incidents):
    for incident in incidents:
        assert incident.sources
        for source in incident.sources:
            assert source.url.startswith("https://")


def test_every_failure_class_has_an_expected_guard(incidents):
    for incident in incidents:
        assert incident.failure_class in EXPECTED_CONTAINMENT


def test_no_guards_means_every_incident_reproduces(incidents):
    """If an incident does not reproduce without guards, its scenario is wrong."""
    result = run_gate(incidents, null_chain())
    assert result.contained == 0, f"did not reproduce: {[e.incident_id for e in result.escapes]}"


def test_the_reference_chain_contains_every_incident(incidents):
    result = run_gate(incidents, reference_chain())
    assert result.ok, "escaped: " + ", ".join(
        f"{e.incident_id} ({e.reason})" for e in result.escapes
    )
    assert result.containment_rate == 1.0


def test_every_reference_guard_is_load_bearing(incidents):
    """A guard the corpus never exercises is a guard you have no evidence for."""
    result = run_gate(incidents, reference_chain())
    assert result.unexercised_guards() == ()


@pytest.mark.parametrize("failure_class", [
    FailureClass.DESTRUCTIVE_ACTION,
    FailureClass.UNGROUNDED_OUTPUT,
    FailureClass.PROMPT_INJECTION,
    FailureClass.RUNAWAY_LOOP,
    FailureClass.STATE_HALLUCINATION,
])
def test_the_corpus_covers_the_main_failure_classes(incidents, failure_class):
    assert any(i.failure_class is failure_class for i in incidents)


def test_each_scenario_names_a_guard_that_actually_contains_it(incidents):
    """`must_be_contained_by` is a claim; this checks it against the harness."""
    from agent_incident_corpus.guards import (
        ApprovalGate,
        BudgetCap,
        GroundingGate,
        GuardChain,
        ProvenanceFilter,
        ScopeLimiter,
        VerificationGate,
    )
    available = {
        "approval_gate": ApprovalGate(),
        "budget_cap": BudgetCap(max_cost_usd=10.0, max_steps=50),
        "provenance_filter": ProvenanceFilter(),
        "verification_gate": VerificationGate(),
        "grounding_gate": GroundingGate(),
        "scope_limiter": ScopeLimiter(allowed=("db://staging",)),
    }
    for incident in incidents:
        named = incident.scenario.must_be_contained_by
        assert named, f"{incident.id}: no guard claimed"
        contained_by = [
            name for name in named
            if replay(incident.scenario, GuardChain((available[name],))).contained
        ]
        assert contained_by, f"{incident.id}: none of {named} actually contains it"


def test_stats_agree_with_the_corpus(incidents):
    stats = summarise(incidents)
    assert stats.total == len(incidents)
    assert sum(stats.by_failure_class.values()) == len(incidents)
    assert sum(stats.by_severity.values()) == len(incidents)
    assert stats.sources_per_incident >= 1.0

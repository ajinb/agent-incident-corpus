from agent_incident_corpus.guards import (
    ApprovalGate,
    BudgetCap,
    GuardChain,
    null_chain,
)
from agent_incident_corpus.replay import replay
from agent_incident_corpus.scenario import Harm, Scenario, ToolCall


def _destructive_scenario():
    return Scenario(
        id="s", description="d",
        steps=(ToolCall("read"), ToolCall("drop", destructive=True, harmful=True)),
        harm=Harm("harmful_step_allowed"),
    )


def test_harm_occurs_without_guards():
    result = replay(_destructive_scenario(), null_chain())
    assert result.escaped
    assert "drop" in result.harm_reason


def test_harm_is_contained_by_the_right_guard():
    result = replay(_destructive_scenario(), GuardChain((ApprovalGate(),)))
    assert result.contained
    assert result.blocked_by == ("approval_gate",)
    assert result.harm_reason is None


def test_a_block_halts_the_run():
    """A control that stops an action stops the agent, not just that one call."""
    scenario = Scenario(
        id="s", description="d",
        steps=(ToolCall("drop", destructive=True, harmful=True), ToolCall("cleanup")),
        harm=Harm("harmful_step_allowed"),
    )
    result = replay(scenario, GuardChain((ApprovalGate(),)))
    assert len(result.outcomes) == 1
    assert result.steps_allowed == 0


def test_cost_accumulates_across_repeats():
    scenario = Scenario(
        id="s", description="d", steps=(ToolCall("infer", cost_usd=1.0),),
        harm=Harm("cost_exceeds", usd=5.0), repeat=10,
    )
    result = replay(scenario, null_chain())
    assert result.total_cost_usd == 10.0
    assert result.escaped


def test_budget_cap_contains_a_loop():
    scenario = Scenario(
        id="s", description="d", steps=(ToolCall("infer", cost_usd=1.0),),
        harm=Harm("cost_exceeds", usd=5.0), repeat=100,
    )
    result = replay(scenario, GuardChain((BudgetCap(max_cost_usd=3.0, max_steps=1000),)))
    assert result.contained
    assert result.total_cost_usd <= 3.0


def test_steps_exceed_predicate():
    scenario = Scenario(
        id="s", description="d", steps=(ToolCall("step"),),
        harm=Harm("steps_exceed", n=3), repeat=10,
    )
    assert replay(scenario, null_chain()).escaped
    assert replay(scenario, GuardChain((BudgetCap(max_steps=2),))).contained


def test_replay_is_deterministic():
    scenario = _destructive_scenario()
    assert replay(scenario, null_chain()) == replay(scenario, null_chain())

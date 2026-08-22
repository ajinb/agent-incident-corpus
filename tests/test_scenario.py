import pytest

from agent_incident_corpus.scenario import Harm, Scenario, ToolCall


def test_tool_call_defaults_are_safe():
    call = ToolCall("read")
    assert call.destructive is False
    assert call.provenance == "user"
    assert call.grounded is True
    assert call.harmful is False


def test_tool_call_rejects_unknown_fields():
    with pytest.raises(ValueError, match="unknown ToolCall fields"):
        ToolCall.from_dict({"tool": "x", "destructve": True})


@pytest.mark.parametrize("harm", [
    {"type": "cost_exceeds"},
    {"type": "steps_exceed"},
])
def test_harm_requires_its_threshold(harm):
    with pytest.raises(ValueError):
        Harm.from_dict(harm)


def test_harm_rejects_unknown_types():
    with pytest.raises(ValueError, match="unknown harm type"):
        Harm(type="vibes")


def test_scenario_requires_steps():
    with pytest.raises(ValueError, match="at least one step"):
        Scenario(id="s", description="d", steps=(), harm=Harm("steps_exceed", n=1))


def test_scenario_requires_a_harmful_step_for_that_predicate():
    with pytest.raises(ValueError, match="no step is marked harmful"):
        Scenario(
            id="s", description="d", steps=(ToolCall("x"),), harm=Harm("harmful_step_allowed")
        )


def test_scenario_rejects_zero_repeat():
    with pytest.raises(ValueError, match="repeat must be at least 1"):
        Scenario(
            id="s", description="d", steps=(ToolCall("x"),),
            harm=Harm("steps_exceed", n=1), repeat=0,
        )


def test_total_steps_accounts_for_repeat():
    scenario = Scenario(
        id="s", description="d", steps=(ToolCall("a"), ToolCall("b")),
        harm=Harm("steps_exceed", n=1), repeat=10,
    )
    assert scenario.total_steps == 20


def test_from_dict_round_trips():
    scenario = Scenario.from_dict({
        "id": "s", "description": "d",
        "steps": [{"tool": "drop", "destructive": True, "harmful": True}],
        "harm": {"type": "harmful_step_allowed"},
        "must_be_contained_by": ["approval_gate"],
    })
    assert scenario.steps[0].destructive is True
    assert scenario.must_be_contained_by == ("approval_gate",)

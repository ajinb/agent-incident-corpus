import pytest

from agent_incident_corpus.guards import (
    ApprovalGate,
    BudgetCap,
    GroundingGate,
    GuardChain,
    NullGuard,
    ProvenanceFilter,
    RunState,
    ScopeLimiter,
    VerificationGate,
    reference_chain,
)
from agent_incident_corpus.scenario import ToolCall


@pytest.fixture
def state():
    return RunState()


class TestApprovalGate:
    def test_blocks_unapproved_destructive_calls(self, state):
        verdict = ApprovalGate().inspect(ToolCall("drop_db", destructive=True), state)
        assert not verdict.allowed
        assert verdict.guard == "approval_gate"

    def test_allows_approved_destructive_calls(self, state):
        call = ToolCall("drop_db", destructive=True, approved=True)
        assert ApprovalGate().inspect(call, state).allowed

    def test_ignores_read_only_calls(self, state):
        assert ApprovalGate().inspect(ToolCall("list_tables"), state).allowed


class TestBudgetCap:
    def test_blocks_when_the_next_step_would_exceed_the_ceiling(self):
        state = RunState(cost_usd=9.6)
        verdict = BudgetCap(max_cost_usd=10.0).inspect(ToolCall("infer", cost_usd=0.5), state)
        assert not verdict.allowed

    def test_is_a_ceiling_not_a_bill(self):
        """The check happens before the spend, or it is just observation."""
        state = RunState(cost_usd=0.0)
        assert not BudgetCap(max_cost_usd=1.0).inspect(ToolCall("infer", cost_usd=5.0), state).allowed

    def test_blocks_on_step_count(self):
        state = RunState(steps_allowed=50)
        assert not BudgetCap(max_steps=50).inspect(ToolCall("infer"), state).allowed

    def test_allows_inside_budget(self, state):
        assert BudgetCap().inspect(ToolCall("infer", cost_usd=0.01), state).allowed


class TestProvenanceFilter:
    def test_blocks_calls_driven_by_tool_output(self, state):
        call = ToolCall("x", provenance="tool_output")
        assert not ProvenanceFilter().inspect(call, state).allowed

    @pytest.mark.parametrize("provenance", ["user", "system", "model"])
    def test_allows_trusted_origins(self, provenance, state):
        assert ProvenanceFilter().inspect(ToolCall("x", provenance=provenance), state).allowed

    def test_the_model_deciding_its_next_step_is_not_an_injection(self, state):
        """Blocking this would mask every other guard and prove nothing."""
        assert ProvenanceFilter().inspect(ToolCall("drop", provenance="model"), state).allowed


class TestVerificationGate:
    def test_blocks_action_on_an_unverified_belief(self, state):
        call = ToolCall("move", asserted_state="dir exists", verified=False)
        assert not VerificationGate().inspect(call, state).allowed

    def test_allows_once_verified(self, state):
        call = ToolCall("move", asserted_state="dir exists", verified=True)
        assert VerificationGate().inspect(call, state).allowed

    def test_ignores_calls_that_assert_nothing(self, state):
        assert VerificationGate().inspect(ToolCall("ls"), state).allowed


class TestGroundingGate:
    def test_blocks_ungrounded_assertions(self, state):
        assert not GroundingGate().inspect(ToolCall("reply", grounded=False), state).allowed

    def test_allows_grounded_assertions(self, state):
        assert GroundingGate().inspect(ToolCall("reply", grounded=True), state).allowed


class TestScopeLimiter:
    def test_denies_by_default(self, state):
        assert not ScopeLimiter().inspect(ToolCall("read", resource="db://prod"), state).allowed

    def test_allows_declared_prefixes(self, state):
        guard = ScopeLimiter(allowed=("db://staging",))
        assert guard.inspect(ToolCall("read", resource="db://staging/users"), state).allowed

    def test_ignores_calls_naming_no_resource(self, state):
        assert ScopeLimiter().inspect(ToolCall("think"), state).allowed


def test_null_guard_allows_everything(state):
    call = ToolCall("drop_db", destructive=True, provenance="tool_output", grounded=False)
    assert NullGuard().inspect(call, state).allowed


class TestGuardChain:
    def test_first_block_wins(self, state):
        chain = GuardChain((ProvenanceFilter(), ApprovalGate()))
        call = ToolCall("drop_db", destructive=True, provenance="tool_output")
        assert chain.inspect(call, state).guard == "provenance_filter"

    def test_empty_chain_allows(self, state):
        assert GuardChain().inspect(ToolCall("drop_db", destructive=True), state).allowed

    def test_reference_chain_omits_scope_limiter(self):
        """A permissive default allowlist would let scope scenarios pass for the wrong reason."""
        assert "scope_limiter" not in reference_chain().names

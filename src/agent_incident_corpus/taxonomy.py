"""The classification vocabulary.

Failure classes describe *what the agent did wrong*. Contributing factors describe *what
was missing that let it*. The split matters: the class tells you which incident you are
looking at, the factors tell you which control would have stopped it — and only the second
one is actionable.

Grounded in the 2026 taxonomy literature (planning / tool / retrieval / reasoning / policy
splits) but narrowed to failures that a platform control can actually contain.
"""

from __future__ import annotations

from enum import Enum


class FailureClass(str, Enum):
    """What went wrong."""

    #: An irreversible operation ran without a human in the loop.
    DESTRUCTIVE_ACTION = "destructive_action"
    #: The agent asserted something its sources did not support, and it was acted on.
    UNGROUNDED_OUTPUT = "ungrounded_output"
    #: Untrusted content arriving through a tool result steered the agent's next actions.
    PROMPT_INJECTION = "prompt_injection"
    #: The agent looped without a budget, consuming spend or wall-clock without progress.
    RUNAWAY_LOOP = "runaway_loop"
    #: The agent acted on a belief about the world that was false and never verified.
    STATE_HALLUCINATION = "state_hallucination"
    #: The agent used credentials or reach beyond what the task required.
    SCOPE_ESCALATION = "scope_escalation"
    #: The agent's own toolchain was tampered with upstream of the user.
    SUPPLY_CHAIN = "supply_chain"


class ContributingFactor(str, Enum):
    """What was missing. These map one-to-one onto the reference guards."""

    NO_APPROVAL_GATE = "no_approval_gate"
    NO_BUDGET_CAP = "no_budget_cap"
    OVERBROAD_CREDENTIALS = "overbroad_credentials"
    NO_VERIFICATION_STEP = "no_verification_step"
    UNTRUSTED_TOOL_OUTPUT = "untrusted_tool_output"
    NO_GROUNDING_CHECK = "no_grounding_check"
    NO_BACKUP_ISOLATION = "no_backup_isolation"
    NO_DRY_RUN = "no_dry_run"


class Severity(str, Enum):
    """Realised impact, not potential impact.

    Rated on what actually happened as publicly reported. An attack that was defanged by a
    formatting bug is LOW even though its intent was CRITICAL — the corpus records outcomes,
    and inflating them would make the severity column useless for prioritisation.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Autonomy(str, Enum):
    """How much rope the agent had when it failed."""

    SUGGEST = "suggest"
    ACT_WITH_APPROVAL = "act_with_approval"
    AUTONOMOUS = "autonomous"


class SourceKind(str, Enum):
    """Provenance strength, strongest first. See CONTRIBUTING.md."""

    INCIDENT_DATABASE = "incident_database"
    COURT = "court"
    VENDOR = "vendor"
    REPOSITORY = "repository"
    POSTMORTEM = "postmortem"
    PRESS = "press"


#: Which guard is expected to contain which class. Used by the gate to explain failures.
EXPECTED_CONTAINMENT: dict[FailureClass, str] = {
    FailureClass.DESTRUCTIVE_ACTION: "approval_gate",
    FailureClass.UNGROUNDED_OUTPUT: "grounding_gate",
    FailureClass.PROMPT_INJECTION: "provenance_filter",
    FailureClass.RUNAWAY_LOOP: "budget_cap",
    FailureClass.STATE_HALLUCINATION: "verification_gate",
    FailureClass.SCOPE_ESCALATION: "scope_limiter",
    FailureClass.SUPPLY_CHAIN: "approval_gate",
}

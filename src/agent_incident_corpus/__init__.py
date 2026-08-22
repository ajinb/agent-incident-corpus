"""agent-incident-corpus — public AI-agent failures as a replayable regression suite."""

from .gate import GateResult, run_gate
from .guards import (
    ApprovalGate,
    BudgetCap,
    GroundingGate,
    GuardChain,
    NullGuard,
    ProvenanceFilter,
    ScopeLimiter,
    VerificationGate,
    null_chain,
    reference_chain,
)
from .loader import corpus_dir, load_corpus, load_incident
from .replay import ReplayResult, replay
from .scenario import Harm, Scenario, ToolCall
from .schema import Incident, Source, ValidationError
from .stats import CorpusStats, summarise
from .taxonomy import (
    EXPECTED_CONTAINMENT,
    Autonomy,
    ContributingFactor,
    FailureClass,
    Severity,
    SourceKind,
)

__version__ = "0.1.0"

__all__ = [
    "EXPECTED_CONTAINMENT", "ApprovalGate", "Autonomy", "BudgetCap", "ContributingFactor",
    "CorpusStats", "FailureClass", "GateResult", "GroundingGate", "GuardChain", "Harm",
    "Incident", "NullGuard", "ProvenanceFilter", "ReplayResult", "Scenario", "ScopeLimiter",
    "Severity", "Source", "SourceKind", "ToolCall", "ValidationError", "VerificationGate",
    "corpus_dir", "load_corpus", "load_incident", "null_chain", "reference_chain", "replay",
    "run_gate", "summarise",
]

"""The paper's measured study: E1-E4.

Reproduces every table in "From Incident to Failing Build: Incident-Derived Regression
Testing for AI-Agent Guardrails". Deterministic by construction — the corpus replays a
fixed scenario per incident through a fixed guard chain, so there are no seeds and no
dispersion to report. That is a property of a regression gate, not a shortcut: a CI gate
that returned a distribution would be useless as a gate.

    python examples/paper_study.py
"""

from __future__ import annotations

from itertools import combinations

from agent_incident_corpus import (
    BudgetCap,
    GuardChain,
    ProvenanceFilter,
    load_corpus,
    null_chain,
    reference_chain,
    run_gate,
)

INCIDENTS = load_corpus()
REFERENCE = reference_chain()


def _rule(title: str) -> None:
    print(f"\n{title}\n{'=' * len(title)}")


def e1_containment() -> None:
    """E1 — the baseline. Same incidents, same replay, only the chain differs."""
    _rule("E1  containment: unguarded vs reference chain")
    print(f"{'chain':<20}{'contained':>11}{'escaped':>9}{'rate':>8}")
    for label, chain in (("none", null_chain()), ("reference", REFERENCE)):
        r = run_gate(INCIDENTS, chain)
        print(f"{label:<20}{r.contained:>11}{len(r.escapes):>9}{r.containment_rate:>7.0%}")

    unexercised = run_gate(INCIDENTS, REFERENCE).unexercised_guards()
    print(f"\nguards never fired in the reference chain: {unexercised or '(none)'}")


def e2_necessity() -> None:
    """E2 — leave-one-out. Which historical failures does dropping each control readmit?"""
    _rule("E2  guard necessity: leave-one-out ablation")
    baseline = run_gate(INCIDENTS, REFERENCE)
    print(f"{'guard removed':<22}{'contained':>11}{'readmitted':>12}  incidents")
    print(f"{'(none)':<22}{baseline.contained:>11}{0:>12}")

    for guard in REFERENCE.guards:
        reduced = GuardChain(tuple(g for g in REFERENCE.guards if g is not guard))
        r = run_gate(INCIDENTS, reduced)
        ids = [e.incident_id for e in r.escapes]
        classes = sorted({e.failure_class.value for e in r.escapes})
        print(f"{guard.name:<22}{r.contained:>11}{len(ids):>12}  "
              f"{', '.join(classes) if classes else '-'}")


def e3_minimal_sufficient() -> None:
    """E3 — is the reference chain minimal, or is it carrying a passenger?

    Exhaustive over all 31 non-empty subsets of the five reference guards. A subset is
    *sufficient* if it contains all ten incidents, and *minimal* if no proper subset of it
    is also sufficient.
    """
    _rule("E3  minimal sufficient chains (exhaustive over 2^5 - 1 subsets)")
    guards = list(REFERENCE.guards)
    sufficient: list[frozenset[str]] = []

    for size in range(1, len(guards) + 1):
        for combo in combinations(guards, size):
            r = run_gate(INCIDENTS, GuardChain(tuple(combo)))
            if r.ok:
                sufficient.append(frozenset(g.name for g in combo))

    minimal = [
        s for s in sufficient
        if not any(other < s for other in sufficient)
    ]

    print(f"sufficient subsets: {len(sufficient)} of {2 ** len(guards) - 1}")
    print(f"minimal sufficient: {len(minimal)}\n")
    for s in sorted(minimal, key=lambda x: (len(x), sorted(x))):
        print(f"  size {len(s)}:  {', '.join(sorted(s))}")

    redundant = {g.name for g in guards} - set().union(*minimal) if minimal else set()
    print(f"\nin no minimal chain (carried for defence in depth only): "
          f"{', '.join(sorted(redundant)) if redundant else '(none)'}")


def e4_configuration_drift() -> None:
    """E4 — the realistic failure. Guards present, but loosened until they stop biting.

    Absence is the easy case and CI already catches it. The failure mode that ships is a
    control that is still in the chain, still green, and no longer load-bearing, because
    someone widened a parameter to unblock a workflow. Only the two parameterised guards
    can drift this way; the other three are binary predicates with nothing to widen.
    """
    _rule("E4  configuration drift: present but loosened")
    others = tuple(
        g for g in REFERENCE.guards
        if g.name not in ("provenance_filter", "budget_cap")
    )
    # The realistic loosening: an engineer whose workflow the filter blocked adds the
    # provenance it was blocking to the trusted set. `tool_output` is the value the corpus
    # actually carries — trusting a label no incident uses would measure nothing.
    TRUST_TOOL = ("user", "system", "model", "tool_output")

    print(f"{'prov':<6}{'cost':>8}{'steps':>7}{'contained':>11}{'readmitted':>12}  incidents")
    for loosen_prov in (False, True):
        for cost in (10.0, 100.0, 1000.0):
            for steps in (50, 500):
                prov = ProvenanceFilter(trusted=TRUST_TOOL) if loosen_prov else ProvenanceFilter()
                chain = GuardChain(
                    others + (prov, BudgetCap(max_cost_usd=cost, max_steps=steps))
                )
                r = run_gate(INCIDENTS, chain)
                ids = [e.incident_id.split("-", 2)[2][:22] for e in r.escapes]
                flag = "loose" if loosen_prov else "tight"
                print(f"{flag:<6}{cost:>8.0f}{steps:>7}{r.contained:>11}"
                      f"{len(r.escapes):>12}  {', '.join(ids)}")


if __name__ == "__main__":
    print(f"agent-incident-corpus paper study - {len(INCIDENTS)} incidents, "
          f"{len(REFERENCE.guards)} reference guards")
    e1_containment()
    e2_necessity()
    e3_minimal_sufficient()
    e4_configuration_drift()

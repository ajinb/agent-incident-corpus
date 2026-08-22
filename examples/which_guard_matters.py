"""Drop one guard at a time and see which incidents come back.

This is the useful form of the question. "Do we have guardrails" is unanswerable; "which
historical failure modes does removing this control let back in" is a number.
"""

from agent_incident_corpus import GuardChain, load_corpus, reference_chain, run_gate

incidents = load_corpus()
full = reference_chain()
baseline = run_gate(incidents, full)

print(f"{'guard removed':<22}{'contained':>11}{'regressions':>13}  incidents")
print(f"{'(none)':<22}{baseline.contained:>11}{0:>13}")

backstopped = []
for guard in full.guards:
    reduced = GuardChain(tuple(g for g in full.guards if g is not guard))
    result = run_gate(incidents, reduced)
    regressions = [e.incident_id for e in result.escapes]
    if not regressions:
        backstopped.append(guard.name)
    print(f"{guard.name:<22}{result.contained:>11}{len(regressions):>13}  "
          f"{', '.join(r[:18] for r in regressions)}")

if backstopped:
    print(
        f"\n{', '.join(backstopped)} fires in the full chain but removing it changes nothing: "
        "every incident it catches is also caught by a later guard. That is defence in depth, "
        "not waste — but it does mean the corpus carries no evidence that it is independently "
        "necessary. An incident that only it can contain is a wanted contribution."
    )

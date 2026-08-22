"""Ten public incidents. One variable: what was allowed to say no.

Each incident carries a synthetic reproduction of its failure *mode* — not a replay of the
real event, which nobody outside the affected companies has traces for. The question the
harness answers is narrow and useful: would this guard configuration have contained it?
"""

from agent_incident_corpus import load_corpus, null_chain, reference_chain, run_gate

incidents = load_corpus()

for label, chain in (("no guards", null_chain()), ("reference", reference_chain())):
    result = run_gate(incidents, chain)
    print(f"\n{label}: contained {result.contained}/{result.total} "
          f"({result.containment_rate:.0%})")
    for escape in result.escapes:
        print(f"  escaped  {escape.incident_id}")
        print(f"           {escape.reason}")
        print(f"           would need: {escape.expected_guard}")

"""agent-incidents command-line interface."""

from __future__ import annotations

import argparse
import json
import sys

from .gate import run_gate
from .guards import null_chain, reference_chain
from .loader import load_corpus
from .schema import ValidationError
from .stats import summarise

_CHAINS = {"reference": reference_chain, "none": null_chain}


def cmd_validate(args) -> int:
    try:
        incidents = load_corpus()
    except (ValidationError, FileNotFoundError) as exc:
        print(f"corpus invalid: {exc}", file=sys.stderr)
        return 1

    weak = [i.id for i in incidents if i.strongest_source.kind.value in ("press", "postmortem")]
    print(f"ok — {len(incidents)} incidents validated")
    if weak:
        print(f"note — {len(weak)} rest on press/postmortem sourcing only:")
        for incident_id in weak:
            print(f"       {incident_id}")
        if args.strict and args.fail_on_weak:
            return 1
    return 0


def cmd_list(args) -> int:
    incidents = load_corpus()
    if args.json:
        print(json.dumps([
            {"id": i.id, "date": i.date, "failure_class": i.failure_class.value,
             "severity": i.severity.value, "title": i.title}
            for i in incidents
        ], indent=2))
        return 0
    print(f"{'date':<12}{'class':<22}{'sev':<10}title")
    for i in incidents:
        print(f"{i.date:<12}{i.failure_class.value:<22}{i.severity.value:<10}{i.title[:60]}")
    return 0


def cmd_show(args) -> int:
    incidents = {i.id: i for i in load_corpus()}
    incident = incidents.get(args.incident_id)
    if incident is None:
        print(f"no such incident: {args.incident_id}", file=sys.stderr)
        return 1

    print(f"{incident.title}\n{'=' * len(incident.title)}")
    print(f"id        {incident.id}")
    print(f"date      {incident.date}")
    print(f"system    {incident.system}")
    print(f"class     {incident.failure_class.value}   severity {incident.severity.value}")
    print(f"factors   {', '.join(f.value for f in incident.contributing_factors)}")
    print(f"\n{incident.summary}\n")
    print(f"blast radius: {incident.blast_radius}\n")
    print("sources:")
    for source in incident.sources:
        print(f"  [{source.kind.value}] {source.title}\n    {source.url}")
    return 0


def cmd_stats(args) -> int:
    stats = summarise(load_corpus())
    if args.json:
        print(json.dumps(stats.__dict__, indent=2, default=str))
        return 0

    print(f"{stats.total} incidents, {stats.source_count} sources "
          f"({stats.sources_per_incident:.1f} per incident)\n")
    for heading, table in (
        ("failure class", stats.by_failure_class),
        ("severity", stats.by_severity),
        ("contributing factor", stats.by_contributing_factor),
        ("year", {str(k): v for k, v in stats.by_year.items()}),
    ):
        print(heading)
        for key, count in table.items():
            print(f"  {key:<26}{count:>3}  {'#' * count}")
        print()
    return 0


def cmd_gate(args) -> int:
    incidents = load_corpus()
    chain = _CHAINS[args.guards]()
    result = run_gate(incidents, chain)

    if args.json:
        print(json.dumps({
            "guards": list(result.guards),
            "total": result.total,
            "contained": result.contained,
            "containment_rate": result.containment_rate,
            "ok": result.ok,
            "escapes": [
                {"incident_id": e.incident_id, "failure_class": e.failure_class.value,
                 "reason": e.reason, "expected_guard": e.expected_guard}
                for e in result.escapes
            ],
        }, indent=2))
        return 0 if result.ok else 1

    print(f"guards: {', '.join(result.guards)}")
    print(f"contained {result.contained}/{result.total} ({result.containment_rate:.0%})\n")
    if result.escapes:
        print("escaped:")
        for escape in result.escapes:
            print(f"  {escape.incident_id}")
            print(f"    {escape.reason}")
            print(f"    expected containment: {escape.expected_guard}")
    unexercised = result.unexercised_guards()
    if unexercised:
        print(f"\nnote — never fired, so untested by this corpus: {', '.join(unexercised)}")
    return 0 if result.ok else 1


def cmd_demo(args) -> int:
    incidents = load_corpus()
    print(f"agent-incident-corpus — {len(incidents)} public incidents, replayed offline\n")
    print(f"{'guard chain':<16}{'contained':>12}{'escaped':>10}")
    for label in ("none", "reference"):
        result = run_gate(incidents, _CHAINS[label]())
        print(f"{label:<16}{result.contained:>12}{result.total - result.contained:>10}")
    print("\nThe same ten incidents. The only variable is what was allowed to say no.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", default=argparse.SUPPRESS,
                        help="machine-readable output")

    parser = argparse.ArgumentParser(
        prog="agent-incidents",
        description="A replayable corpus of public AI-agent production failures.",
        parents=[common],
    )
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("demo", parents=[common], help="containment with and without guards (default)")
    sub.add_parser("list", parents=[common], help="list every incident")
    sub.add_parser("stats", parents=[common], help="what the corpus covers")

    validate = sub.add_parser("validate", parents=[common], help="validate every record")
    validate.add_argument("--strict", action="store_true", help="report weak sourcing")
    validate.add_argument("--fail-on-weak", action="store_true",
                          help="with --strict, exit non-zero on press-only sourcing")

    gate = sub.add_parser("gate", parents=[common],
                          help="fail if a guard chain does not contain every incident")
    gate.add_argument("--guards", choices=sorted(_CHAINS), default="reference")

    show = sub.add_parser("show", parents=[common], help="print one incident in full")
    show.add_argument("incident_id")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.json = getattr(args, "json", False)
    handlers = {
        "demo": cmd_demo, "list": cmd_list, "stats": cmd_stats, "validate": cmd_validate,
        "gate": cmd_gate, "show": cmd_show, None: cmd_demo,
    }
    return handlers[args.command](args)


if __name__ == "__main__":
    sys.exit(main())

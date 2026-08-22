import json

import pytest

from agent_incident_corpus.cli import main


@pytest.mark.parametrize("argv", [[], ["demo"], ["list"], ["stats"], ["validate"]])
def test_read_only_commands_succeed(argv, capsys):
    assert main(argv) == 0
    assert capsys.readouterr().out.strip()


@pytest.mark.parametrize("argv", [["list"], ["stats"]])
def test_json_output_parses(argv, capsys):
    assert main(argv + ["--json"]) == 0
    assert json.loads(capsys.readouterr().out)


def test_gate_passes_with_the_reference_guards(capsys):
    assert main(["gate", "--guards", "reference"]) == 0
    assert "contained 10/10" in capsys.readouterr().out


def test_gate_fails_with_no_guards(capsys):
    assert main(["gate", "--guards", "none"]) == 1
    out = capsys.readouterr().out
    assert "escaped:" in out
    assert "expected containment:" in out


def test_gate_json_reports_the_escapes(capsys):
    assert main(["gate", "--guards", "none", "--json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert len(payload["escapes"]) == payload["total"]


def test_show_prints_an_incident(capsys):
    assert main(["show", "2025-07-replit-agent-production-database-deletion"]) == 0
    out = capsys.readouterr().out
    assert "incidentdatabase.ai" in out
    assert "destructive_action" in out


def test_show_rejects_an_unknown_id(capsys):
    assert main(["show", "nope"]) == 1


def test_validate_strict_reports_weak_sourcing(capsys):
    assert main(["validate", "--strict"]) == 0
    assert "press/postmortem" in capsys.readouterr().out

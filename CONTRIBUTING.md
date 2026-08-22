# Contributing

Two very different kinds of contribution live here, with different bars.

## Adding an incident (the high bar)

A corpus is only worth citing if every entry is traceable. Use the **New incident** issue
template, then open a PR adding one `corpus/<id>.json`.

**Sourcing.** At least one source is required, and the strongest one is what the record is
judged on. In descending order of strength:

1. `incident_database` — an [AI Incident Database](https://incidentdatabase.ai) entry
2. `court` — a ruling or filing
3. `vendor` — the affected vendor's own security bulletin or postmortem
4. `repository` — the project's own issue tracker or advisory
5. `postmortem` — a named first-hand account by the affected party
6. `press` — established outlets

A vendor blog summarising someone else's reporting is not a source; link what it summarises.
`agent-incidents validate --strict` reports every record resting on press or postmortem
sourcing alone. Those are accepted, but they are flagged, and upgrading one to a primary
source is a welcome PR on its own.

**Writing.** Summaries are original prose written for this project — never excerpts from the
linked reporting. Neutral and specific: what the agent did, what was missing, what it cost.
No vendor-bashing, no "this proves AI is dangerous", no speculation about intent. If a
detail is disputed in the reporting, say so or leave it out.

**Severity is rated on realised impact, not potential impact.** An attack defanged by a
formatting bug is `low` even if its intent was `critical`. Inflating severity makes the
column useless for the prioritisation it exists to support.

**Scenarios.** Every incident carries a synthetic reproduction of its failure *mode* — see
the note in the README. It must:

- reproduce under `null_chain()` (`agent-incidents gate --guards none` must show it escaping)
- be contained by at least one guard it names in `must_be_contained_by`
- stay small. Four steps is usually plenty.

`tests/test_corpus.py` enforces all three. A scenario that cannot fail without guards is not
testing anything.

## Changing the tooling (the normal bar)

- `pip install -e ".[dev]"`, then `pytest -q` and `ruff check src tests examples`.
- Guards are small and obvious by design. A guard that needs configuration to be safe by
  default is the wrong shape — see `ScopeLimiter`, which denies by default and is deliberately
  left out of the reference chain for that reason.
- No runtime dependencies in the core.
- The harness is deterministic: no clocks, no randomness, no network. Keep it that way.

## What is out of scope

- Incidents with no public source. Anonymised war stories belong in a blog post, not here.
- Model benchmark results. This corpus is about the platform controls around a model, not
  the model.
- Anything involving a named individual as the subject rather than a system.

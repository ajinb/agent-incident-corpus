---
name: New incident
about: Propose an incident for the corpus
---

**What happened** (2–4 sentences, neutral, no vendor-bashing)

**Date** (YYYY-MM-DD — when it happened, not when it was reported)

**System** (product / framework / model, as publicly reported)

**Failure class** (see `taxonomy.py`)

**Sources** — at least one required. Strongest first: AI Incident Database entry, court
ruling, vendor security bulletin or postmortem, the project's own issue tracker, then
established press. A vendor blog summarising someone else's reporting is not a source.

**Scenario** — how would you reproduce this failure *mode* synthetically? Which guard
should have contained it?

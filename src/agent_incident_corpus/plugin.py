"""pytest plugin.

Ask for the `incident` fixture and your test runs once per corpus entry. Nothing else about
your test session changes — the plugin only acts on tests that request its fixtures, so
installing this package cannot alter an unrelated suite.

    def test_my_guards_contain_it(incident, my_chain):
        assert replay(incident.scenario, my_chain).contained
"""

from __future__ import annotations

import pytest

from .guards import null_chain, reference_chain
from .loader import load_corpus


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "incident" in metafunc.fixturenames:
        incidents = load_corpus()
        metafunc.parametrize("incident", incidents, ids=[i.id for i in incidents])


@pytest.fixture(scope="session")
def corpus():
    """Every incident, validated, sorted by date."""
    return load_corpus()


@pytest.fixture(scope="session")
def reference_guards():
    """The bundled reference guard chain."""
    return reference_chain()


@pytest.fixture(scope="session")
def no_guards():
    """The baseline every incident in the corpus was running."""
    return null_chain()

"""The rule catalogue is generated, and the committed copy must match (SPEC 2.5)."""

from __future__ import annotations

from api.catalogue import CATALOGUE_PATH, check, render
from api.rules.registry import all_rules


def test_committed_catalogue_matches_the_generated_one() -> None:
    """CI fails here when a rule changes and docs/saannot.md was not regenerated."""
    ok, diff = check()

    assert ok, (
        "docs/saannot.md has drifted from the rule metadata.\n"
        "Run: python -m api.catalogue --write\n\n" + diff
    )


def test_rendering_is_deterministic() -> None:
    """Same rules in, same bytes out — otherwise the drift check is noise."""
    assert render() == render()


def test_every_rule_appears_in_the_catalogue() -> None:
    text = CATALOGUE_PATH.read_text(encoding="utf-8")

    for registered in all_rules():
        assert registered.meta.id in text, registered.meta.id
        assert registered.meta.title_fi in text, registered.meta.id


def test_the_catalogue_says_the_figures_are_invented() -> None:
    """No official figures are claimed, anywhere they are printed (SPEC 2.6)."""
    text = CATALOGUE_PATH.read_text(encoding="utf-8")

    assert "keksitty tätä demoa varten" in text
    assert "eivät ole voimassa olevia lakisääteisiä rajoja" in text


def test_the_catalogue_warns_against_editing_it_by_hand() -> None:
    assert CATALOGUE_PATH.read_text(encoding="utf-8").startswith("# Sääntöluettelo\n\n<!--")

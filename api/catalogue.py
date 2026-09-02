"""Generator for ``docs/saannot.md``.

The rule catalogue is documentation nobody maintains by hand. Everything in it
comes from rule metadata and from ``seeds/limits.py``, so a rule that changes its
title, its required fields or its possible outcomes changes the document, and CI
fails if the committed copy has drifted.

    python -m api.catalogue --write     # regenerate the committed file
    python -m api.catalogue --check     # exit 1 if it has drifted
"""

from __future__ import annotations

import argparse
import difflib
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path

from api.rules import engine as _engine  # noqa: F401  importing it registers every rule
from api.rules.registry import ALL_FORMS, RegisteredRule, all_rules
from api.rules.types import Limits
from api.texts import fi
from seeds.limits import DEMO_LIMITS

CATALOGUE_PATH = Path(__file__).resolve().parent.parent / "docs" / "saannot.md"

#: Fixed order so the document is stable across runs.
FORM_ORDER: tuple[str, ...] = (
    "vapaarahoitteinen",
    "lyhyt_korkotuki",
    "tarveharkintainen",
    "asumisoikeus",
)

#: Capital region first: it is the larger stock and the tighter market.
GROUP_ORDER: tuple[str, ...] = ("paakaupunkiseutu", "muu_suomi")

FORM_INTROS = {
    "vapaarahoitteinen": (
        "Avoin haku. Tuloja verrataan vain vuokranmaksukykyyn, eikä varallisuutta tai "
        "asunnontarvetta kysytä."
    ),
    "lyhyt_korkotuki": (
        "Ruokakunnan tulot tarkistetaan. Varallisuutta ja asunnontarvetta ei kysytä, ja "
        "sääntö LYHYT-EI-VARALLISUUS-01 valvoo sitä."
    ),
    "tarveharkintainen": (
        "Tulot, varallisuus ja asunnontarve arvioidaan, ja hakijat asetetaan keskenään "
        "järjestykseen."
    ),
    "asumisoikeus": (
        "Tulorajaa ei ole. Hakemiseen tarvitaan järjestysnumero, ja asunto tarjotaan "
        "pienimmän numeron mukaan."
    ),
}


def _rules_declared_for(housing_form: str) -> tuple[RegisteredRule, ...]:
    """Rules declared for exactly this form, without the cross-cutting ones."""
    return tuple(r for r in all_rules() if housing_form in r.meta.housing_forms)


def _cross_cutting() -> tuple[RegisteredRule, ...]:
    return tuple(r for r in all_rules() if ALL_FORMS in r.meta.housing_forms)


def _requires_cell(requires: Sequence[str]) -> str:
    if not requires:
        return "–"
    return ", ".join(fi.REQUIRED_FIELD_LABELS[name] for name in requires)


def _outcomes_cell(outcomes: Sequence[str]) -> str:
    if not outcomes:
        return "järjestysnumero"
    return ", ".join(fi.OUTCOME_LABELS[value].lower() for value in outcomes)


def _rule_section(registered: RegisteredRule) -> list[str]:
    meta = registered.meta
    return [
        f"#### {meta.id} — {meta.title_fi}",
        "",
        meta.description_fi,
        "",
        f"- **Laji:** {fi.RULE_KIND_LABELS[meta.kind]}",
        f"- **Tarvitsee hakemukselta:** {_requires_cell(meta.requires)}",
        f"- **Mahdolliset lopputulokset:** {_outcomes_cell(meta.outcomes)}",
        "",
    ]


def _summary_table(rules: Iterable[RegisteredRule]) -> list[str]:
    lines = [
        "| Tunnus | Sääntö | Laji | Tarvitsee hakemukselta |",
        "| --- | --- | --- | --- |",
    ]
    for registered in rules:
        meta = registered.meta
        lines.append(
            f"| `{meta.id}` | {meta.title_fi} | {fi.RULE_KIND_LABELS[meta.kind]} "
            f"| {_requires_cell(meta.requires)} |"
        )
    lines.append("")
    return lines


def _limits_section(limits: Limits) -> list[str]:
    lines = [
        "## Käytetyt rajat",
        "",
        "**Kaikki alla olevat luvut on keksitty tätä demoa varten.** Ne eivät ole voimassa "
        "olevia lakisääteisiä rajoja eivätkä peräisin mistään asuntotoimijalta. Luvut ovat "
        "tiedostossa `seeds/limits.py`, joka on ainoa paikka koko projektissa, jossa niitä "
        "säilytetään.",
        "",
        "### Tulorajat, bruttotulot euroa kuukaudessa",
        "",
    ]
    for form in FORM_ORDER:
        table = limits.income_limits.get(form)
        if table is None:
            lines.append(f"**{fi.HOUSING_FORM_LABELS[form]}:** ei tulorajaa.")
            lines.append("")
            continue
        groups = [g for g in GROUP_ORDER if g in table]
        sizes = sorted({size for group in groups for size in table[group]})
        lines.append(f"**{fi.HOUSING_FORM_LABELS[form]}**")
        lines.append("")
        lines.append("| Ruokakunnan koko | " + " | ".join(_group_label(g) for g in groups) + " |")
        lines.append("| --- | " + " | ".join("---" for _ in groups) + " |")
        for size in sizes:
            cells = " | ".join(fi.euros(table[group][size]) for group in groups)
            lines.append(f"| {fi.people(size)} | {cells} |")
        extra = limits.income_limit_per_extra_person[form]
        lines.append(
            f"| jokainen seuraava henkilö | {' | '.join([fi.euros(extra)] * len(groups))} |"
        )
        lines.append("")

    lines.extend(
        [
            "### Varallisuusrajat",
            "",
            "| Asumismuoto | Ruokakunnan varallisuus enintään |",
            "| --- | --- |",
        ]
    )
    for form in FORM_ORDER:
        limit = limits.asset_limit(form)
        value = fi.euros(limit) if limit is not None else "ei varallisuusrajaa"
        lines.append(f"| {fi.HOUSING_FORM_LABELS[form]} | {value} |")
    lines.append("")

    lines.extend(
        [
            "### Muut rajat",
            "",
            "| Raja | Arvo |",
            "| --- | --- |",
            "| Vuokran enimmäisosuus bruttotuloista "
            f"| {fi.percent(limits.max_rent_share_of_gross_income)} |",
            f"| Ikä, josta alkaen varallisuusraja ei koske asumisoikeushakijaa "
            f"| {limits.wealth_exemption_age} vuotta |",
            f"| Täysi-ikäisyys | {limits.adult_age} vuotta |",
            f"| Asukkaita enintään huonetta kohden | {limits.max_persons_per_room} |",
            "| Huoneiden ero, josta asunnosta huomautetaan suureksi "
            f"| {limits.underuse_rooms_margin} |",
            f"| Hakemuksen voimassaolo | {limits.application_validity_months} kuukautta |",
            f"| Asumisoikeusnumeron muoto | `{limits.order_number_pattern}` |",
            "",
        ]
    )
    return lines


def _group_label(group: str) -> str:
    return {
        "paakaupunkiseutu": "Pääkaupunkiseutu",
        "muu_suomi": "Muu Suomi",
    }.get(group, group)


def render(limits: Limits = DEMO_LIMITS) -> str:
    """Render the whole catalogue. Deterministic: same rules in, same bytes out."""
    lines: list[str] = [
        "# Sääntöluettelo",
        "",
        "<!-- Tämä tiedosto on generoitu. Älä muokkaa käsin. -->",
        "<!-- Generated file. Do not edit by hand; run `python -m api.catalogue --write`. -->",
        "",
        "Jokainen asunnon kelpoisuuspäätös syntyy jostakin alla olevasta säännöstä ja "
        "kertoo hakijalle sekä säännön tunnuksen että sen arvon, joka päätökseen johti.",
        "",
        "Lopputuloksia on kolme: **kelpoinen**, **puuttuvat tiedot** ja **ei kelpoinen**. "
        "Puuttuva tieto ei ole hylkäys vaan pyyntö täydentää hakemusta.",
        "",
        "Sarake *Tarvitsee hakemukselta* kertoo, mitä hakulomake kysyy, kun hakemuksella on "
        "kyseisen asumismuodon asunto. Lomake kootaan näistä tiedoista, joten uusi sääntö "
        "muuttaa lomaketta ilman erillistä muutosta käyttöliittymään.",
        "",
        "## Kaikki säännöt",
        "",
        *_summary_table(all_rules()),
        "## Säännöt asumismuodoittain",
        "",
    ]

    for form in FORM_ORDER:
        lines.append(f"### {fi.HOUSING_FORM_LABELS[form].capitalize()}")
        lines.append("")
        lines.append(FORM_INTROS[form])
        lines.append("")
        for registered in _rules_declared_for(form):
            lines.extend(_rule_section(registered))

    lines.append("### Kaikkia asumismuotoja koskevat säännöt")
    lines.append("")
    for registered in _cross_cutting():
        lines.extend(_rule_section(registered))

    lines.extend(_limits_section(limits))

    return "\n".join(lines).rstrip("\n") + "\n"


def check(path: Path = CATALOGUE_PATH) -> tuple[bool, str]:
    """Compare the committed catalogue with a freshly rendered one."""
    expected = render()
    if not path.exists():
        return False, f"{path} does not exist. Run: python -m api.catalogue --write"
    actual = path.read_text(encoding="utf-8")
    if actual == expected:
        return True, ""
    diff = difflib.unified_diff(
        actual.splitlines(keepends=True),
        expected.splitlines(keepends=True),
        fromfile=f"{path.name} (committed)",
        tofile=f"{path.name} (generated)",
    )
    return False, "".join(diff)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true", help="regenerate docs/saannot.md")
    group.add_argument("--check", action="store_true", help="fail if the committed copy drifted")
    args = parser.parse_args(argv)

    if args.write:
        CATALOGUE_PATH.parent.mkdir(parents=True, exist_ok=True)
        CATALOGUE_PATH.write_text(render(), encoding="utf-8")
        print(f"Wrote {CATALOGUE_PATH}")
        return 0

    ok, diff = check()
    if ok:
        print("docs/saannot.md is up to date.")
        return 0
    print(diff, file=sys.stderr)
    print(
        "docs/saannot.md has drifted from the rule metadata. Run: python -m api.catalogue --write",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

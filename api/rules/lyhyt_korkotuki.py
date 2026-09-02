"""Short-term interest subsidy rental stock (lyhyen korkotuen vuokra-asunto).

Household income is checked. Wealth and housing need are not — and the second
rule here exists to keep it that way.
"""

from __future__ import annotations

from api.rules.registry import guard_rule, rule
from api.rules.types import ApplicationSnapshot, Limits, Outcome, UnitSnapshot
from api.texts import fi

FORM = "lyhyt_korkotuki"

#: Snapshot field names that must not be consulted when deciding a short-term
#: subsidy apartment. Names are the attribute names a rule author would type, on
#: the application and on a household member alike.
FORBIDDEN_FIELDS = frozenset({"total_assets", "assets_eur", "housing_need", "urgency_note"})

#: Shown to the applicant instead of the attribute names.
FORBIDDEN_FIELD_LABELS = {
    "total_assets": "varallisuus",
    "assets_eur": "varallisuus",
    "housing_need": "asunnontarve",
    "urgency_note": "asunnontarpeen kuvaus",
}


@rule(
    id="LYHYT-TULO-01",
    housing_forms=[FORM],
    requires=["household_income", "household_size"],
    title_fi="Ruokakunnan tulot enintään tulorajan suuruiset",
    description_fi=(
        "Ruokakunnan bruttotulot verrataan tulorajaan, joka määräytyy ruokakunnan koon ja "
        "kohteen sijaintikunnan mukaan."
    ),
)
def income_within_limit(
    snapshot: ApplicationSnapshot, unit: UnitSnapshot, limits: Limits
) -> Outcome:
    size = snapshot.household_size()
    income = snapshot.total_monthly_income()
    limit = limits.income_limit(FORM, unit.city, max(size, 1))
    if limit is None:  # pragma: no cover - the form always has a limit table
        raise ValueError(f"no income limit configured for {FORM}")
    if income is None:
        return Outcome(
            outcome="puuttuvat_tiedot",
            rule_id="LYHYT-TULO-01",
            message_fi=fi.income_missing(),
            evidence={
                "puuttuva_tieto": "ruokakunnan_bruttotulot",
                "tuloraja_eur_kk": limit,
                "ruokakunnan_koko": size,
            },
        )
    evidence = {
        "ruokakunnan_bruttotulot_eur_kk": income,
        "tuloraja_eur_kk": limit,
        "ruokakunnan_koko": size,
        "kunta": unit.city,
    }
    if income <= limit:
        return Outcome(
            outcome="kelpoinen",
            rule_id="LYHYT-TULO-01",
            message_fi=fi.income_within_limit(income, limit, size),
            evidence=evidence,
        )
    return Outcome(
        outcome="ei_kelpoinen",
        rule_id="LYHYT-TULO-01",
        message_fi=fi.income_over_limit(income, limit, size),
        evidence=evidence,
    )


@guard_rule(
    id="LYHYT-EI-VARALLISUUS-01",
    housing_forms=[FORM],
    requires=[],
    title_fi="Varallisuutta ja asunnontarvetta ei kysytä",
    description_fi=(
        "Tarkistaa, ettei päätöstä tehtäessä luettu varallisuus- tai asunnontarvetietoja. "
        "Sääntö on olemassa, jotta regressio, joka alkaa kysyä pienituloisilta hakijoilta "
        "varallisuustietoja, kaatuu testissä."
    ),
)
def no_wealth_or_need_consulted(
    snapshot: ApplicationSnapshot,
    unit: UnitSnapshot,
    limits: Limits,
    consulted: frozenset[str],
) -> Outcome:
    # `consulted` is recorded by the engine while the other rules for this
    # apartment run, and handed here as an ordinary argument. The rule observes
    # nothing on its own and stays a pure function of its inputs.
    breaches = sorted(consulted & FORBIDDEN_FIELDS)
    if breaches:
        return Outcome(
            outcome="ei_kelpoinen",
            rule_id="LYHYT-EI-VARALLISUUS-01",
            message_fi=fi.forbidden_fields_consulted(
                FORBIDDEN_FIELD_LABELS[name] for name in breaches
            ),
            evidence={"kielletyt_luetut_kentat": breaches},
        )
    return Outcome(
        outcome="kelpoinen",
        rule_id="LYHYT-EI-VARALLISUUS-01",
        message_fi=fi.no_wealth_check_needed(),
        evidence={
            "kielletyt_luetut_kentat": [],
            "luetut_kentat": sorted(consulted),
        },
    )

"""Free-financed rental stock (vapaarahoitteinen vuokra-asunto).

Open to anyone. There is no income ceiling, no wealth test and no housing-need
assessment — only the ability to pay the rent and the deposit, plus a credit
question that is asked but is not on its own disqualifying.

Evidence keys are Finnish because the evidence is shown to the applicant on the
decisions screen, not only written to a log.
"""

from __future__ import annotations

from api.rules.registry import rule
from api.rules.types import ApplicationSnapshot, Limits, Outcome, UnitSnapshot
from api.texts import fi

FORM = "vapaarahoitteinen"


def _require_rent(unit: UnitSnapshot) -> None:
    """Sale units are never part of an application; they are offered on, not applied for.

    Reaching a rent rule without a rent is a programming error rather than an
    applicant-facing state, so it raises instead of inventing an outcome.
    """
    if unit.listing_type != "vuokra" or unit.rent_eur is None:
        raise ValueError(f"unit {unit.id} is not a rental unit and cannot be applied for")


@rule(
    id="VAPAA-MAKSU-01",
    housing_forms=[FORM],
    requires=["household_income"],
    title_fi="Tulot riittävät vuokraan",
    description_fi=(
        "Vuokra saa olla enintään määritellyn osuuden ruokakunnan bruttotuloista. "
        "Tulon lähdettä ei eroteta: etuudet lasketaan samalla tavalla kuin palkka."
    ),
)
def rent_within_income(
    snapshot: ApplicationSnapshot, unit: UnitSnapshot, limits: Limits
) -> Outcome:
    _require_rent(unit)
    assert unit.rent_eur is not None
    income = snapshot.total_monthly_income()
    if income is None:
        return Outcome(
            outcome="puuttuvat_tiedot",
            rule_id="VAPAA-MAKSU-01",
            message_fi=fi.rent_income_missing(),
            evidence={
                "puuttuva_tieto": "ruokakunnan_bruttotulot",
                "vuokra_eur_kk": unit.rent_eur,
            },
        )
    share = limits.max_rent_share_of_gross_income
    max_rent = income * share
    evidence = {
        "vuokra_eur_kk": unit.rent_eur,
        "ruokakunnan_bruttotulot_eur_kk": income,
        "enimmaisosuus_tuloista": share,
        "enimmaisvuokra_eur_kk": max_rent,
    }
    if unit.rent_eur <= max_rent:
        return Outcome(
            outcome="kelpoinen",
            rule_id="VAPAA-MAKSU-01",
            message_fi=fi.rent_within_income(unit.rent_eur, income, share),
            evidence=evidence,
        )
    return Outcome(
        outcome="ei_kelpoinen",
        rule_id="VAPAA-MAKSU-01",
        message_fi=fi.rent_over_income(unit.rent_eur, income, share, max_rent),
        evidence=evidence,
    )


@rule(
    id="VAPAA-VAKUUS-01",
    housing_forms=[FORM],
    requires=["deposit_acknowledged"],
    title_fi="Vakuus on hyväksytty",
    description_fi="Hakija on vahvistanut, että voi maksaa asunnon vakuuden.",
)
def deposit_acknowledged(
    snapshot: ApplicationSnapshot, unit: UnitSnapshot, limits: Limits
) -> Outcome:
    acknowledged = snapshot.deposit_acknowledged
    if acknowledged is None:
        return Outcome(
            outcome="puuttuvat_tiedot",
            rule_id="VAPAA-VAKUUS-01",
            message_fi=fi.deposit_unanswered(unit.deposit_eur),
            evidence={
                "puuttuva_tieto": "vakuuden_hyvaksyminen",
                "vakuus_eur": unit.deposit_eur,
            },
        )
    if acknowledged:
        return Outcome(
            outcome="kelpoinen",
            rule_id="VAPAA-VAKUUS-01",
            message_fi=fi.deposit_acknowledged(unit.deposit_eur),
            evidence={"vakuus_hyvaksytty": True, "vakuus_eur": unit.deposit_eur},
        )
    return Outcome(
        outcome="ei_kelpoinen",
        rule_id="VAPAA-VAKUUS-01",
        message_fi=fi.deposit_declined(unit.deposit_eur),
        evidence={"vakuus_hyvaksytty": False, "vakuus_eur": unit.deposit_eur},
    )


@rule(
    id="VAPAA-LUOTTO-01",
    housing_forms=[FORM],
    requires=["credit_record"],
    title_fi="Luottotiedot on selvitetty",
    description_fi=(
        "Maksuhäiriömerkintä ei yksin johda hylkäämiseen. Merkinnän kohdalla hakijalta "
        "pyydetään selvitys, jolloin päätös on puuttuvat tiedot eikä ei kelpoinen."
    ),
    outcomes=["kelpoinen", "puuttuvat_tiedot"],
)
def credit_record(snapshot: ApplicationSnapshot, unit: UnitSnapshot, limits: Limits) -> Outcome:
    # The asymmetry here is deliberate and is the point of the rule. An
    # unanswered credit question and a credit default both produce
    # puuttuvat_tiedot, never ei_kelpoinen: a default marker is a reason to ask
    # for context, not a reason to refuse someone a home. Only a human decides
    # what the explanation is worth, and this demo has no such step, so the rule
    # has no path to ei_kelpoinen at all.
    flag = snapshot.credit_default_flag
    if flag is None:
        return Outcome(
            outcome="puuttuvat_tiedot",
            rule_id="VAPAA-LUOTTO-01",
            message_fi=fi.credit_unanswered(),
            evidence={"puuttuva_tieto": "luottotiedot"},
        )
    if flag:
        return Outcome(
            outcome="puuttuvat_tiedot",
            rule_id="VAPAA-LUOTTO-01",
            message_fi=fi.credit_default_needs_context(),
            evidence={
                "maksuhairiomerkinta": True,
                "pyydetty_lisatieto": "selvitys_merkinnan_taustasta",
            },
        )
    return Outcome(
        outcome="kelpoinen",
        rule_id="VAPAA-LUOTTO-01",
        message_fi=fi.credit_clean(),
        evidence={"maksuhairiomerkinta": False},
    )

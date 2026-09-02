"""Needs-assessed rental stock (tarveharkintainen vuokra-asunto).

Income, wealth and housing need are all assessed, and applicants are ranked
against each other rather than judged only on their own merits.
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from api.rules.registry import ranking_rule, rule
from api.rules.types import ApplicationSnapshot, Limits, Outcome, Ranked, UnitSnapshot
from api.texts import fi

FORM = "tarveharkintainen"

#: Most urgent first. An applicant who has not stated a situation sorts after
#: everyone who has, rather than being dropped from the queue.
URGENCY_ORDER = {
    "asunnoton": 0,
    "irtisanottu": 1,
    "ahtaasti": 2,
    "ei_tarvetta": 3,
}
_UNSTATED_URGENCY = len(URGENCY_ORDER)

#: Missing money sorts last without inventing a threshold to compare against.
_UNKNOWN_AMOUNT = Decimal("Infinity")


@rule(
    id="TARVE-TULO-01",
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
            rule_id="TARVE-TULO-01",
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
            rule_id="TARVE-TULO-01",
            message_fi=fi.income_within_limit(income, limit, size),
            evidence=evidence,
        )
    return Outcome(
        outcome="ei_kelpoinen",
        rule_id="TARVE-TULO-01",
        message_fi=fi.income_over_limit(income, limit, size),
        evidence=evidence,
    )


@rule(
    id="TARVE-VARALLISUUS-01",
    housing_forms=[FORM],
    requires=["assets"],
    title_fi="Ruokakunnan varallisuus enintään varallisuusrajan suuruinen",
    description_fi="Ruokakunnan yhteenlaskettu varallisuus verrataan varallisuusrajaan.",
)
def assets_within_limit(
    snapshot: ApplicationSnapshot, unit: UnitSnapshot, limits: Limits
) -> Outcome:
    limit = limits.asset_limit(FORM)
    if limit is None:  # pragma: no cover - the form always has an asset limit
        raise ValueError(f"no asset limit configured for {FORM}")
    assets = snapshot.total_assets()
    if assets is None:
        return Outcome(
            outcome="puuttuvat_tiedot",
            rule_id="TARVE-VARALLISUUS-01",
            message_fi=fi.assets_missing(),
            evidence={
                "puuttuva_tieto": "ruokakunnan_varallisuus",
                "varallisuusraja_eur": limit,
            },
        )
    evidence = {"ruokakunnan_varallisuus_eur": assets, "varallisuusraja_eur": limit}
    if assets <= limit:
        return Outcome(
            outcome="kelpoinen",
            rule_id="TARVE-VARALLISUUS-01",
            message_fi=fi.assets_within_limit(assets, limit),
            evidence=evidence,
        )
    return Outcome(
        outcome="ei_kelpoinen",
        rule_id="TARVE-VARALLISUUS-01",
        message_fi=fi.assets_over_limit(assets, limit),
        evidence=evidence,
    )


@rule(
    id="TARVE-TARVE-01",
    housing_forms=[FORM],
    requires=["housing_need"],
    title_fi="Asunnontarve on ilmoitettu",
    description_fi=(
        "Hakijan on kerrottava asuntotilanteensa. Vastaus 'ei erityistä asunnontarvetta' on "
        "kelvollinen vastaus eikä estä hakemista; se vaikuttaa hakijoiden järjestykseen "
        "säännössä TARVE-SIJOITUS-01."
    ),
    outcomes=["kelpoinen", "puuttuvat_tiedot"],
)
def housing_need_stated(
    snapshot: ApplicationSnapshot, unit: UnitSnapshot, limits: Limits
) -> Outcome:
    # The rule checks that a situation has been stated, not that the situation
    # is urgent enough. Urgency is a ranking question, and turning "no special
    # need" into a rejection is not something the specification asks for.
    situation = snapshot.housing_need
    if situation is None:
        return Outcome(
            outcome="puuttuvat_tiedot",
            rule_id="TARVE-TARVE-01",
            message_fi=fi.need_missing(),
            evidence={"puuttuva_tieto": "asunnontarve"},
        )
    if situation == "ei_tarvetta":
        return Outcome(
            outcome="kelpoinen",
            rule_id="TARVE-TARVE-01",
            message_fi=fi.need_none_stated(),
            evidence={"asunnontarve": situation, "vaikuttaa_jarjestykseen": True},
        )
    return Outcome(
        outcome="kelpoinen",
        rule_id="TARVE-TARVE-01",
        message_fi=fi.need_stated(situation),
        evidence={"asunnontarve": situation, "vaikuttaa_jarjestykseen": True},
    )


@ranking_rule(
    id="TARVE-SIJOITUS-01",
    housing_forms=[FORM],
    requires=["housing_need", "assets", "household_income"],
    title_fi="Hakijoiden järjestys tarveharkinnassa",
    description_fi=(
        "Järjestys: kiireellisin asunnontarve ensin, sitten pienin varallisuus, sitten "
        "pienimmät tulot. Yhtä kiireelliset hakemukset järjestetään jättöpäivän mukaan, "
        "ei koskaan satunnaisesti."
    ),
)
def needs_ranking(
    applicants: Sequence[ApplicationSnapshot], unit: UnitSnapshot, limits: Limits
) -> Sequence[Ranked]:
    def sort_key(snapshot: ApplicationSnapshot) -> tuple[int, Decimal, Decimal, float, int]:
        assets = snapshot.total_assets()
        income = snapshot.total_monthly_income()
        return (
            URGENCY_ORDER.get(snapshot.housing_need or "", _UNSTATED_URGENCY),
            assets if assets is not None else _UNKNOWN_AMOUNT,
            income if income is not None else _UNKNOWN_AMOUNT,
            snapshot.created_at.timestamp(),
            snapshot.id,
        )

    ordered = sorted(applicants, key=sort_key)
    ranked: list[Ranked] = []
    for position, snapshot in enumerate(ordered, start=1):
        assets = snapshot.total_assets()
        income = snapshot.total_monthly_income()
        ranked.append(
            Ranked(
                rank=position,
                application_id=snapshot.id,
                rule_id="TARVE-SIJOITUS-01",
                message_fi=fi.needs_ranking(position, snapshot.housing_need, assets, income),
                evidence={
                    "asunnontarve": snapshot.housing_need,
                    "ruokakunnan_varallisuus_eur": assets,
                    "ruokakunnan_bruttotulot_eur_kk": income,
                    "hakemus_jatetty": snapshot.created_at,
                },
            )
        )
    return tuple(ranked)

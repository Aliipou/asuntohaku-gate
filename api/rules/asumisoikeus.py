"""Right-of-occupancy stock (asumisoikeusasunto).

No income limit. An order number issued by the state housing authority is
required, selection follows that number, and the wealth limit does not apply to
a household whose adult applicants have all reached the exemption age.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from api.rules.registry import ranking_rule, rule
from api.rules.types import ApplicationSnapshot, Limits, Outcome, Ranked, UnitSnapshot
from api.texts import fi

FORM = "asumisoikeus"


def _is_well_formed(order_number: str, limits: Limits) -> bool:
    return re.fullmatch(limits.order_number_pattern, order_number) is not None


@rule(
    id="ASO-JARJ-01",
    housing_forms=[FORM],
    requires=["order_number"],
    title_fi="Asumisoikeusnumero on annettu ja oikean muotoinen",
    description_fi=(
        "Asumisoikeusasuntoon tarvitaan järjestysnumero. Puuttuva numero on puuttuva tieto, "
        "ei hylkäys; väärän muotoinen numero hylätään."
    ),
)
def order_number_present(
    snapshot: ApplicationSnapshot, unit: UnitSnapshot, limits: Limits
) -> Outcome:
    number = snapshot.order_number
    if number is None or not number.strip():
        return Outcome(
            outcome="puuttuvat_tiedot",
            rule_id="ASO-JARJ-01",
            message_fi=fi.order_number_missing(),
            evidence={"puuttuva_tieto": "asumisoikeusnumero"},
        )
    number = number.strip()
    if not _is_well_formed(number, limits):
        return Outcome(
            outcome="ei_kelpoinen",
            rule_id="ASO-JARJ-01",
            message_fi=fi.order_number_malformed(number),
            evidence={"asumisoikeusnumero": number, "vaadittu_muoto": limits.order_number_pattern},
        )
    return Outcome(
        outcome="kelpoinen",
        rule_id="ASO-JARJ-01",
        message_fi=fi.order_number_accepted(number),
        evidence={"asumisoikeusnumero": number},
    )


@ranking_rule(
    id="ASO-JARJ-02",
    housing_forms=[FORM],
    requires=["order_number"],
    title_fi="Hakijoiden järjestys asumisoikeusnumeron mukaan",
    description_fi=(
        "Asunto tarjotaan pienimmän järjestysnumeron mukaan. Hakijat, joilta numero puuttuu "
        "tai on väärän muotoinen, eivät ole jonossa: heidät pysäyttää sääntö ASO-JARJ-01."
    ),
)
def order_number_ranking(
    applicants: Sequence[ApplicationSnapshot], unit: UnitSnapshot, limits: Limits
) -> Sequence[Ranked]:
    eligible = [
        snapshot
        for snapshot in applicants
        if snapshot.order_number and _is_well_formed(snapshot.order_number.strip(), limits)
    ]

    def sort_key(snapshot: ApplicationSnapshot) -> tuple[int, str, int]:
        number = (snapshot.order_number or "").strip()
        # Shorter numbers sort first, then lexicographically. For the fixed-width
        # format this is the numeric order without assuming the digits parse.
        return (len(number), number, snapshot.id)

    ranked: list[Ranked] = []
    for position, snapshot in enumerate(sorted(eligible, key=sort_key), start=1):
        number = (snapshot.order_number or "").strip()
        ranked.append(
            Ranked(
                rank=position,
                application_id=snapshot.id,
                rule_id="ASO-JARJ-02",
                message_fi=fi.order_ranking(position, number),
                evidence={"asumisoikeusnumero": number},
            )
        )
    return tuple(ranked)


@rule(
    id="ASO-VARALLISUUS-01",
    housing_forms=[FORM],
    requires=["assets", "household_size"],
    title_fi="Varallisuusraja, josta yli 55-vuotiaat on vapautettu",
    description_fi=(
        "Ruokakunnan varallisuus verrataan varallisuusrajaan. Jos ruokakunnan kaikki "
        "aikuiset hakijat ovat täyttäneet vapautusiän, raja ei koske hakemusta ja päätös on "
        "kelpoinen riippumatta varallisuudesta."
    ),
)
def assets_within_limit_unless_exempt(
    snapshot: ApplicationSnapshot, unit: UnitSnapshot, limits: Limits
) -> Outcome:
    limit = limits.asset_limit(FORM)
    if limit is None:  # pragma: no cover - the form always has an asset limit
        raise ValueError(f"no asset limit configured for {FORM}")

    ages = snapshot.ages()
    if ages is not None:
        adults = [age for age in ages if age >= limits.adult_age]
        # The exemption is checked before the assets are, because when it
        # applies the assets are not needed to decide at all.
        if adults and all(age >= limits.wealth_exemption_age for age in adults):
            return Outcome(
                outcome="kelpoinen",
                rule_id="ASO-VARALLISUUS-01",
                message_fi=fi.assets_exempt_by_age(limits.wealth_exemption_age),
                evidence={
                    "poikkeus": "ikapoikkeus",
                    "vapautusika": limits.wealth_exemption_age,
                    "aikuisten_iat": sorted(adults),
                    "varallisuusraja_eur": limit,
                },
            )

    assets = snapshot.total_assets()
    if assets is None:
        return Outcome(
            outcome="puuttuvat_tiedot",
            rule_id="ASO-VARALLISUUS-01",
            message_fi=fi.assets_missing(),
            evidence={
                "puuttuva_tieto": "ruokakunnan_varallisuus",
                "varallisuusraja_eur": limit,
            },
        )
    if assets <= limit:
        return Outcome(
            outcome="kelpoinen",
            rule_id="ASO-VARALLISUUS-01",
            message_fi=fi.assets_within_limit(assets, limit),
            evidence={"ruokakunnan_varallisuus_eur": assets, "varallisuusraja_eur": limit},
        )
    if ages is None:
        # Over the limit, and we cannot tell whether the exemption applies.
        # That is a question to ask, not a reason to refuse.
        return Outcome(
            outcome="puuttuvat_tiedot",
            rule_id="ASO-VARALLISUUS-01",
            message_fi=fi.birth_years_missing(),
            evidence={
                "puuttuva_tieto": "syntymavuodet",
                "ruokakunnan_varallisuus_eur": assets,
                "varallisuusraja_eur": limit,
                "vapautusika": limits.wealth_exemption_age,
            },
        )
    return Outcome(
        outcome="ei_kelpoinen",
        rule_id="ASO-VARALLISUUS-01",
        message_fi=fi.assets_over_limit(assets, limit),
        evidence={
            "ruokakunnan_varallisuus_eur": assets,
            "varallisuusraja_eur": limit,
            "aikuisten_iat": sorted(age for age in ages if age >= limits.adult_age),
            "vapautusika": limits.wealth_exemption_age,
        },
    )

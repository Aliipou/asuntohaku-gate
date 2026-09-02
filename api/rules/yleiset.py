"""Cross-cutting rules that apply to every housing form."""

from __future__ import annotations

from api.rules.registry import ALL_FORMS, rule
from api.rules.types import ApplicationSnapshot, Limits, Outcome, UnitSnapshot
from api.texts import fi


@rule(
    id="YLEIS-KOKO-01",
    housing_forms=[ALL_FORMS],
    requires=["household_size"],
    title_fi="Ruokakunnan koko suhteessa asunnon kokoon",
    description_fi=(
        "Liian suuri ruokakunta asuntoon on hylkäys. Ruokakuntaan nähden suuri asunto ei ole "
        "este: päätös on kelpoinen ja hakijalle kerrotaan, että suurempi ruokakunta voi saada "
        "etusijan."
    ),
)
def household_fits_unit(
    snapshot: ApplicationSnapshot, unit: UnitSnapshot, limits: Limits
) -> Outcome:
    size = snapshot.household_size()
    if size == 0:
        return Outcome(
            outcome="puuttuvat_tiedot",
            rule_id="YLEIS-KOKO-01",
            message_fi=fi.household_missing(),
            evidence={"puuttuva_tieto": "ruokakunnan_jasenet", "huoneita": unit.rooms},
        )
    max_size = unit.rooms * limits.max_persons_per_room
    evidence = {
        "ruokakunnan_koko": size,
        "huoneita": unit.rooms,
        "enimmaiskoko": max_size,
        "pinta_ala_m2": unit.area_m2,
    }
    if size > max_size:
        return Outcome(
            outcome="ei_kelpoinen",
            rule_id="YLEIS-KOKO-01",
            message_fi=fi.size_too_large(size, unit.rooms, max_size),
            evidence=evidence,
        )
    if unit.rooms - size >= limits.underuse_rooms_margin:
        return Outcome(
            outcome="kelpoinen",
            rule_id="YLEIS-KOKO-01",
            message_fi=fi.size_underused(size, unit.rooms),
            evidence={**evidence, "huomautus": "asunto_suuri_ruokakuntaan_nahden"},
        )
    return Outcome(
        outcome="kelpoinen",
        rule_id="YLEIS-KOKO-01",
        message_fi=fi.size_fits(size, unit.rooms),
        evidence=evidence,
    )


@rule(
    id="YLEIS-VANHENTUNUT-01",
    housing_forms=[ALL_FORMS],
    requires=[],
    title_fi="Hakemuksen voimassaolo",
    description_fi=(
        "Hakemus on voimassa määrätyn ajan jättöpäivästä. Vanhentunut hakemus ei ole hylätty: "
        "kaikkien asuntojen päätökseksi tulee puuttuvat tiedot ja hakijaa pyydetään "
        "vahvistamaan tiedot muokkauslinkistä."
    ),
    outcomes=["kelpoinen", "puuttuvat_tiedot"],
)
def application_still_valid(
    snapshot: ApplicationSnapshot, unit: UnitSnapshot, limits: Limits
) -> Outcome:
    # The engine short-circuits on this rule: when an application has expired,
    # every apartment in the basket gets this outcome and nothing else runs.
    if snapshot.is_expired():
        return Outcome(
            outcome="puuttuvat_tiedot",
            rule_id="YLEIS-VANHENTUNUT-01",
            message_fi=fi.application_expired(snapshot.expires_at),
            evidence={
                "hakemus_jatetty": snapshot.created_at,
                "voimassa_asti": snapshot.expires_at,
                "voimassaolo_kuukautta": limits.application_validity_months,
                "puuttuva_tieto": "tietojen_vahvistus",
            },
        )
    return Outcome(
        outcome="kelpoinen",
        rule_id="YLEIS-VANHENTUNUT-01",
        message_fi=fi.application_valid_until(snapshot.expires_at),
        evidence={
            "voimassa_asti": snapshot.expires_at,
            "voimassaolo_kuukautta": limits.application_validity_months,
        },
    )

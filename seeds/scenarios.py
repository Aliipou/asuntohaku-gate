"""The eight demo scenarios from SPEC section 8.

Each one is chosen to land on a different rule, so that running them end to end
shows the whole catalogue doing its job rather than one happy path repeated.

    python -m seeds.scenarios

They are defined here as snapshots, which is what the rule engine consumes. Step
12.4 loads the same scenarios into the database as preloaded applications so the
README can link to each one by its edit token; the definitions below stay the
single source for both.
"""

from __future__ import annotations

import datetime as dt
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal

from api.app.dates import expiry_for
from api.rules.engine import decide, required_fields
from api.rules.types import ApplicationSnapshot, Limits, MemberSnapshot, UnitSnapshot
from api.texts import fi
from seeds.data import PROPERTIES, PropertySeed, UnitSeed
from seeds.limits import DEMO_LIMITS


@dataclass(frozen=True, slots=True)
class Scenario:
    number: int
    title_fi: str
    explanation: str
    application: ApplicationSnapshot
    units: tuple[UnitSnapshot, ...]
    #: The rule this scenario exists to demonstrate, per SPEC section 8.
    demonstrates: str


def _find(property_name: str, unit_number: str) -> UnitSnapshot:
    for prop in PROPERTIES:
        if prop.name != property_name:
            continue
        for unit in prop.units:
            if unit.unit_number == unit_number:
                return _to_snapshot(prop, unit)
    raise KeyError(f"{property_name} {unit_number} is not in the seed stock")


def _to_snapshot(prop: PropertySeed, unit: UnitSeed) -> UnitSnapshot:
    return UnitSnapshot(
        id=abs(hash((prop.name, unit.unit_number))) % 100_000,
        label=f"{prop.street} {unit.unit_number}, {prop.city}",
        city=prop.city,
        housing_form=prop.housing_form,  # type: ignore[arg-type]
        listing_type=unit.listing_type,  # type: ignore[arg-type]
        rooms=unit.rooms,
        area_m2=unit.area_m2,
        rent_eur=unit.rent_eur,
        price_eur=unit.price_eur,
        deposit_eur=unit.deposit_eur,
    )


def _member(
    role: str = "paahakija",
    *,
    birth_year: int | None = None,
    income: str | None = None,
    assets: str | None = None,
) -> MemberSnapshot:
    return MemberSnapshot(
        role=role,  # type: ignore[arg-type]
        birth_year=birth_year,
        gross_monthly_income_eur=None if income is None else Decimal(income),
        assets_eur=None if assets is None else Decimal(assets),
    )


def _application(
    now: dt.datetime,
    *,
    id: int,
    members: tuple[MemberSnapshot, ...],
    days_ago: int = 5,
    limits: Limits = DEMO_LIMITS,
    housing_need: str | None = None,
    order_number: str | None = None,
    deposit_acknowledged: bool | None = None,
    credit_default_flag: bool | None = None,
) -> ApplicationSnapshot:
    created = now - dt.timedelta(days=days_ago)
    return ApplicationSnapshot(
        id=id,
        evaluated_at=now,
        created_at=created,
        expires_at=expiry_for(created, limits.application_validity_months),
        members=members,
        housing_need=housing_need,  # type: ignore[arg-type]
        order_number=order_number,
        deposit_acknowledged=deposit_acknowledged,
        credit_default_flag=credit_default_flag,
    )


def scenarios(now: dt.datetime, limits: Limits = DEMO_LIMITS) -> tuple[Scenario, ...]:
    """Build all eight scenarios against the given evaluation moment."""
    free_studio = _find("Kalliolan portti", "A 12")
    free_two_room = _find("Kalliolan portti", "B 4")
    needs_assessed = _find("Vallilan verstas", "A 14")
    right_of_occupancy = _find("Suvelan aukio", "A 5")

    # Scenarios 1 and 2 are the same person: someone who has only ever been asked
    # what free-financed stock requires, and so has never given wealth or need
    # data. That is what makes the form visibly grow in scenario 2.
    only_free_financed = _application(
        now,
        id=1,
        members=(_member(birth_year=1990, income="3000"),),
        deposit_acknowledged=True,
        credit_default_flag=False,
    )

    return (
        Scenario(
            number=1,
            title_fi="Yksin hakeva, vain vapaarahoitteinen asunto",
            explanation=(
                "Avoimen kannan asunto. Lomake kysyy vain tulot, vakuuden ja luottotiedot, "
                "ja kaikki kolme ovat kunnossa."
            ),
            application=only_free_financed,
            units=(free_studio,),
            demonstrates="VAPAA-MAKSU-01",
        ),
        Scenario(
            number=2,
            title_fi="Sama hakija lisää tarveharkintaisen asunnon",
            explanation=(
                "Hakemukselle tulee kaksi uutta osiota, varallisuus ja asunnontarve, koska "
                "tarveharkintainen asunto vaatii ne. Vapaarahoitteinen asunto pysyy "
                "kelpoisena, uusi asunto jää odottamaan täydennystä."
            ),
            application=only_free_financed,
            units=(free_studio, needs_assessed),
            demonstrates="TARVE-VARALLISUUS-01",
        ),
        Scenario(
            number=3,
            title_fi="Tulot juuri tarveharkinnan rajan yli",
            explanation=(
                "Sama hakemus, samat asunnot, eri lopputulos asunnoittain: tuloraja "
                "ylittyy tarveharkintaisessa asunnossa, mutta vapaarahoitteinen asunto "
                "ei katso tulorajaa lainkaan."
            ),
            application=_application(
                now,
                id=3,
                members=(_member(birth_year=1988, income="3250", assets="8000"),),
                housing_need="ahtaasti",
                deposit_acknowledged=True,
                credit_default_flag=False,
            ),
            units=(free_studio, needs_assessed),
            demonstrates="TARVE-TULO-01",
        ),
        Scenario(
            number=4,
            title_fi="Varallisuus rajan yli, molemmat hakijat 56-vuotiaita",
            explanation=(
                "Sama varallisuus, kaksi eri sääntöä: asumisoikeusasunnossa yli 55-vuotiaat "
                "on vapautettu varallisuusrajasta, tarveharkinnassa ei ole vastaavaa "
                "poikkeusta."
            ),
            application=_application(
                now,
                id=4,
                members=(
                    _member(birth_year=now.year - 56, income="1400", assets="60000"),
                    _member("toinen", birth_year=now.year - 56, income="1400", assets="60000"),
                ),
                housing_need="ahtaasti",
                order_number="004512",
                deposit_acknowledged=True,
                credit_default_flag=False,
            ),
            units=(right_of_occupancy, needs_assessed),
            demonstrates="ASO-VARALLISUUS-01",
        ),
        Scenario(
            number=5,
            title_fi="Asumisoikeusasunto ilman järjestysnumeroa",
            explanation=(
                "Numero puuttuu, joten päätöstä ei voi tehdä. Se ei ole hylkäys vaan pyyntö "
                "täydentää hakemusta."
            ),
            application=_application(
                now,
                id=5,
                members=(_member(birth_year=1992, income="2600", assets="4000"),),
                housing_need="ahtaasti",
                order_number=None,
                deposit_acknowledged=True,
                credit_default_flag=False,
            ),
            units=(right_of_occupancy,),
            demonstrates="ASO-JARJ-01",
        ),
        Scenario(
            number=6,
            title_fi="Maksuhäiriömerkintä luottotiedoissa",
            explanation=(
                "Merkintä ei hylkää hakemusta. Hakijalta pyydetään selvitys, ja päätökseksi "
                "tulee puuttuvat tiedot."
            ),
            application=_application(
                now,
                id=6,
                members=(_member(birth_year=1995, income="3600"),),
                deposit_acknowledged=True,
                credit_default_flag=True,
            ),
            units=(free_two_room,),
            demonstrates="VAPAA-LUOTTO-01",
        ),
        Scenario(
            number=7,
            title_fi="Viiden hengen ruokakunta hakee yksiötä",
            explanation=(
                "Tulot riittäisivät, mutta asunto on ruokakunnalle liian pieni. Tämä on "
                "hylkäys, ja hakijalle kerrotaan asunnon enimmäiskoko."
            ),
            application=_application(
                now,
                id=7,
                members=(
                    _member(birth_year=1986, income="2200", assets="1500"),
                    _member("toinen", birth_year=1987, income="1800", assets="1500"),
                    _member("muu", birth_year=2012, income="0", assets="0"),
                    _member("muu", birth_year=2015, income="0", assets="0"),
                    _member("muu", birth_year=2019, income="0", assets="0"),
                ),
                housing_need="ahtaasti",
                deposit_acknowledged=True,
                credit_default_flag=False,
            ),
            units=(free_studio,),
            demonstrates="YLEIS-KOKO-01",
        ),
        Scenario(
            number=8,
            title_fi="Neljä kuukautta vanha hakemus",
            explanation=(
                "Hakemus on vanhentunut. Kaikkien asuntojen päätös palautuu puuttuviin "
                "tietoihin ja hakijaa pyydetään vahvistamaan tiedot muokkauslinkistä."
            ),
            application=_application(
                now,
                id=8,
                days_ago=122,
                members=(_member(birth_year=1991, income="2800", assets="6000"),),
                housing_need="ahtaasti",
                order_number="004513",
                deposit_acknowledged=True,
                credit_default_flag=False,
            ),
            units=(free_studio, needs_assessed),
            demonstrates="YLEIS-VANHENTUNUT-01",
        ),
    )


def _format_evidence(evidence: Mapping[str, object]) -> str:
    return " | ".join(f"{key}={fi.evidence_value(key, value)}" for key, value in evidence.items())


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    now = dt.datetime.now(dt.UTC)
    print(f"Päätökset arvioitu {fi.date(now)}.")
    print("Kaikki tiedot ja kaikki rajat on keksitty tätä demoa varten.\n")

    for scenario in scenarios(now):
        print("=" * 78)
        print(f"Skenaario {scenario.number}: {scenario.title_fi}")
        print(f"  {scenario.explanation}\n")

        asked = required_fields(scenario.units)
        print("  Lomake kysyy: " + ", ".join(fi.REQUIRED_FIELD_LABELS[f] for f in asked))
        for field, causes in asked.items():
            apartments = sorted({c.unit_label for c in causes})
            print(f"    - {fi.REQUIRED_FIELD_LABELS[field]}: {', '.join(apartments)}")
        print()

        by_id = {u.id: u for u in scenario.units}
        for decision in decide(scenario.application, scenario.units, DEMO_LIMITS):
            label = by_id[decision.unit_id].label
            print(f"  {label}")
            print(f"    {fi.OUTCOME_LABELS[decision.outcome].upper()}")

            # A blocking row leads with the rule that blocked it. A row where
            # every rule agreed has no single deciding rule, so it does not
            # pretend to have one.
            passed = decision.outcome == "kelpoinen"
            if passed:
                shown = list(decision.all_outcomes)
            else:
                shown = [decision.deciding]
                shown += [o for o in decision.all_outcomes if o is not decision.deciding]

            for index, outcome in enumerate(shown):
                marker = "  >" if index == 0 and not passed else "   "
                print(f"  {marker} {outcome.rule_id}: {outcome.message_fi}")
                print(f"        {_format_evidence(outcome.evidence)}")
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

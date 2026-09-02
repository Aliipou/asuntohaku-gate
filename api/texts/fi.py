"""Every Finnish string the rule engine can produce.

Kept in one module so the wording can be reviewed as prose rather than hunted
through rule bodies. The messages are written to the applicant: second person
singular, active voice, no apology, and they always say what is missing and
where to fix it.

"Ruokakunta" is used rather than "kotitalous" because that is the term Finnish
tenant selection uses.

City names are never inflected. Finnish case endings for place names
(Helsingissä, Vantaalla, Tampereella) cannot be generated safely from a string,
and a wrong ending is exactly what a Finnish reader notices, so the wording is
built to avoid needing one.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterable
from decimal import Decimal

SITUATION_LABELS = {
    "asunnoton": "asunnoton",
    "irtisanottu": "vuokrasopimus irtisanottu",
    "ahtaasti": "asut ahtaasti",
    "ei_tarvetta": "ei erityistä asunnontarvetta",
}

HOUSING_FORM_LABELS = {
    "vapaarahoitteinen": "vapaarahoitteinen vuokra-asunto",
    "lyhyt_korkotuki": "lyhyen korkotuen vuokra-asunto",
    "tarveharkintainen": "tarveharkintainen vuokra-asunto",
    "asumisoikeus": "asumisoikeusasunto",
}

#: One sentence per housing form, saying what it means for the applicant. Shown
#: on the apartment page (SPEC section 7.2).
HOUSING_FORM_EXPLANATIONS = {
    "vapaarahoitteinen": (
        "Tätä asuntoa voi hakea kuka tahansa. Tulojasi katsotaan vain sen verran, että "
        "vuokra on maksettavissa, eikä varallisuutta tai asunnontarvetta kysytä."
    ),
    "lyhyt_korkotuki": (
        "Tähän asuntoon tarkistetaan ruokakunnan tulot. Varallisuutta ja asunnontarvetta ei kysytä."
    ),
    "tarveharkintainen": (
        "Tähän asuntoon arvioidaan ruokakunnan tulot, varallisuus ja asunnontarve, ja "
        "hakijat asetetaan keskenään järjestykseen."
    ),
    "asumisoikeus": (
        "Tähän asuntoon tarvitaan asumisoikeuden järjestysnumero. Tulorajaa ei ole, mutta "
        "varallisuusraja on, ellei ruokakunnan kaikkia aikuisia koske ikäpoikkeus."
    ),
}

OUTCOME_LABELS = {
    "kelpoinen": "Kelpoinen",
    "puuttuvat_tiedot": "Puuttuvat tiedot",
    "ei_kelpoinen": "Ei kelpoinen",
}

#: What the application form calls each adaptive field. The keys are the
#: RequiredField vocabulary the rules declare in their metadata.
REQUIRED_FIELD_LABELS = {
    "household_income": "ruokakunnan tulot",
    "assets": "ruokakunnan varallisuus",
    "housing_need": "asunnontarve",
    "order_number": "asumisoikeusnumero",
    "deposit_acknowledged": "vakuuden hyväksyminen",
    "credit_record": "luottotiedot",
    "household_size": "ruokakunnan koko",
}

RULE_KIND_LABELS = {
    "rule": "kelpoisuussääntö",
    "ranking_rule": "järjestyssääntö",
    "guard_rule": "valvontasääntö",
}


#: Finnish typography groups thousands with a space and keeps the unit on the
#: same line as the number. Written as an escape so it survives an editor that
#: normalises whitespace.
NBSP = " "


def euros(amount: Decimal) -> str:
    """Finnish currency formatting: 1 234,50 €, grouped with non-breaking spaces."""
    quantised = amount.quantize(Decimal("1")) if amount == amount.to_integral_value() else amount
    whole, _, frac = f"{quantised:.2f}".partition(".")
    grouped = f"{int(whole):,}".replace(",", NBSP)
    if frac == "00":
        return f"{grouped}{NBSP}€"
    return f"{grouped},{frac}{NBSP}€"


def date(value: dt.date | dt.datetime) -> str:
    return f"{value.day}.{value.month}.{value.year}"


def people(count: int) -> str:
    """ "1 henki", but "2 henkeä": Finnish takes the partitive from two upwards."""
    return "1 henki" if count == 1 else f"{count} henkeä"


def rooms(count: int) -> str:
    """ "1 huone", but "3 huonetta" — same partitive rule as people()."""
    return "1 huone" if count == 1 else f"{count} huonetta"


def percent(share: Decimal) -> str:
    return f"{(share * 100).quantize(Decimal('1'))}{NBSP}%"


def evidence_value(key: str, value: object) -> str:
    """Format one evidence value for display.

    Evidence keys carry their unit as a suffix, so the same convention formats
    them everywhere: ``_eur`` and ``_eur_kk`` are money, ``_m2`` is an area,
    ``osuus`` is a share. Anything else is shown as it is.
    """
    if isinstance(value, bool) or value is None:
        return {True: "kyllä", False: "ei", None: "ei ilmoitettu"}[value]
    if isinstance(value, Decimal):
        if key.endswith(("_eur", "_eur_kk")):
            return euros(value)
        if key.endswith("_m2"):
            return f"{value.normalize():f}".replace(".", ",") + f"{NBSP}m²"
        if "osuus" in key:
            return percent(value)
        return f"{value.normalize():f}".replace(".", ",")
    if isinstance(value, dt.datetime | dt.date):
        return date(value)
    if isinstance(value, list | tuple):
        return ", ".join(str(item) for item in value) if value else "–"
    return str(value)


def _list(values: Iterable[str]) -> str:
    items = list(values)
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " ja " + items[-1]


# -- VAPAA-MAKSU-01 --------------------------------------------------------


def rent_within_income(rent: Decimal, income: Decimal, share: Decimal) -> str:
    return (
        f"Vuokra {euros(rent)} kuukaudessa mahtuu ruokakuntasi bruttotuloihin "
        f"{euros(income)} kuukaudessa."
    )


def rent_over_income(rent: Decimal, income: Decimal, share: Decimal, max_rent: Decimal) -> str:
    return (
        f"Vuokra {euros(rent)} kuukaudessa on yli {percent(share)} ruokakuntasi bruttotuloista "
        f"{euros(income)}. Näillä tuloilla vuokra voi olla enintään {euros(max_rent)}."
    )


def rent_income_missing() -> str:
    return (
        "Emme voi arvioida vuokranmaksukykyä, koska ruokakunnan bruttotulot puuttuvat. "
        "Täydennä jokaisen jäsenen tulot kohdassa Tulot."
    )


# -- VAPAA-VAKUUS-01 -------------------------------------------------------


def deposit_acknowledged(deposit: Decimal | None) -> str:
    if deposit is None:
        return "Olet hyväksynyt asunnon vakuuden."
    return f"Olet hyväksynyt {euros(deposit)} suuruisen vakuuden."


def deposit_unanswered(deposit: Decimal | None) -> str:
    if deposit is None:
        return "Vahvista kohdassa Vakuus, että voit maksaa asunnon vakuuden."
    return f"Vahvista kohdassa Vakuus, että voit maksaa {euros(deposit)} suuruisen vakuuden."


def deposit_declined(deposit: Decimal | None) -> str:
    if deposit is None:
        return "Et ole hyväksynyt asunnon vakuutta, joten tätä asuntoa ei voi hakea."
    return (
        f"Et ole hyväksynyt {euros(deposit)} suuruista vakuutta, joten tätä asuntoa ei voi hakea."
    )


# -- VAPAA-LUOTTO-01 -------------------------------------------------------


def credit_clean() -> str:
    return "Luottotiedoissasi ei ole maksuhäiriömerkintää."


def credit_unanswered() -> str:
    return "Kerro kohdassa Luottotiedot, onko luottotiedoissasi maksuhäiriömerkintä."


def credit_default_needs_context() -> str:
    return (
        "Luottotiedoissasi on maksuhäiriömerkintä. Kerro lyhyesti, mistä se johtuu, niin "
        "asuntosihteeri käsittelee hakemuksen. Merkintä ei yksin estä asunnon saamista."
    )


# -- income limits (LYHYT-TULO-01, TARVE-TULO-01) ---------------------------


def income_within_limit(income: Decimal, limit: Decimal, size: int) -> str:
    return (
        f"Ruokakunnan bruttotulot {euros(income)} kuukaudessa ovat enintään tulorajan "
        f"{euros(limit)} suuruiset. Raja koskee {size} hengen ruokakuntaa tässä kohteessa."
    )


def income_over_limit(income: Decimal, limit: Decimal, size: int) -> str:
    return (
        f"Ruokakunnan bruttotulot {euros(income)} kuukaudessa ylittävät tulorajan "
        f"{euros(limit)}. Raja koskee {size} hengen ruokakuntaa tässä kohteessa."
    )


def income_missing() -> str:
    return (
        "Emme voi tarkistaa tulorajaa, koska ruokakunnan bruttotulot puuttuvat. "
        "Täydennä jokaisen jäsenen tulot kohdassa Tulot."
    )


# -- LYHYT-EI-VARALLISUUS-01 -----------------------------------------------


def no_wealth_check_needed() -> str:
    return (
        "Tähän asuntoon ei kysytä varallisuutta eikä asunnontarvetta. Päätös perustuu "
        "ilmoittamiisi tuloihin."
    )


def forbidden_fields_consulted(fields: Iterable[str]) -> str:
    return (
        "Hakemuksen käsittelyssä käytettiin tietoja, joita tähän asuntoon ei saa käyttää: "
        f"{_list(fields)}. Ilmoita virheestä, hakemusta ei ole käsitelty oikein."
    )


# -- wealth limits (TARVE-VARALLISUUS-01, ASO-VARALLISUUS-01) --------------


def assets_within_limit(assets: Decimal, limit: Decimal) -> str:
    return (
        f"Ruokakunnan varallisuus {euros(assets)} on enintään varallisuusrajan {euros(limit)} "
        "suuruinen."
    )


def assets_over_limit(assets: Decimal, limit: Decimal) -> str:
    return f"Ruokakunnan varallisuus {euros(assets)} ylittää varallisuusrajan {euros(limit)}."


def assets_missing() -> str:
    return (
        "Emme voi tarkistaa varallisuusrajaa, koska ruokakunnan varallisuustiedot puuttuvat. "
        "Täydennä varallisuus kohdassa Varallisuus."
    )


def assets_exempt_by_age(age: int) -> str:
    return (
        f"Ruokakunnan kaikki aikuiset hakijat ovat täyttäneet {age} vuotta, joten "
        "varallisuusraja ei koske tätä hakemusta."
    )


def birth_years_missing() -> str:
    return (
        "Kerro hakijoiden syntymävuodet kohdassa Ruokakunta, jotta voimme tarkistaa, "
        "koskeeko varallisuusraja hakemustasi."
    )


# -- TARVE-TARVE-01 --------------------------------------------------------


def need_stated(situation: str) -> str:
    return f"Olet kertonut asuntotilanteesi: {SITUATION_LABELS[situation]}."


def need_none_stated() -> str:
    return (
        "Olet kertonut, ettei sinulla ole erityistä asunnontarvetta. Voit hakea asuntoa, "
        "mutta asunnontarve vaikuttaa hakijoiden järjestykseen."
    )


def need_missing() -> str:
    return "Kerro asuntotilanteesi kohdassa Asunnontarve, jotta hakemus voidaan käsitellä."


# -- TARVE-SIJOITUS-01 -----------------------------------------------------


def needs_ranking(
    rank: int, situation: str | None, assets: Decimal | None, income: Decimal | None
) -> str:
    situation_text = SITUATION_LABELS[situation] if situation else "asunnontarvetta ei ilmoitettu"
    assets_text = euros(assets) if assets is not None else "ei ilmoitettu"
    income_text = euros(income) if income is not None else "ei ilmoitettu"
    return (
        f"Sija {rank}. Asuntotilanne: {situation_text}. Varallisuus: {assets_text}. "
        f"Bruttotulot: {income_text}. Yhtä kiireelliset hakemukset järjestetään "
        "jättöpäivän mukaan."
    )


# -- ASO-JARJ-01 / ASO-JARJ-02 ---------------------------------------------


def order_number_accepted(number: str) -> str:
    return f"Asumisoikeusnumero {number} on kirjattu hakemukseesi."


def order_number_missing() -> str:
    return (
        "Asumisoikeusasuntoon tarvitaan Asumisen rahoitus- ja kehittämiskeskuksen antama "
        "järjestysnumero. Lisää numero kohdassa Asumisoikeusnumero."
    )


def order_number_malformed(number: str) -> str:
    return (
        f"Asumisoikeusnumero {number} ei kelpaa. Tässä demossa numerossa on kuusi numeroa, "
        "esimerkiksi 123456."
    )


def order_ranking(rank: int, number: str) -> str:
    return (
        f"Sija {rank}. Asumisoikeusnumero {number}. Asunto tarjotaan pienimmän "
        "järjestysnumeron mukaan."
    )


# -- YLEIS-KOKO-01 ---------------------------------------------------------


def size_fits(size: int, room_count: int) -> str:
    return f"{size} hengen ruokakunta sopii {room_count} huoneen asuntoon."


def size_too_large(size: int, room_count: int, max_size: int) -> str:
    return (
        f"Asunnossa on {rooms(room_count)}, joten siihen valitaan enintään {max_size} hengen "
        f"ruokakunta. Ruokakunnassasi on {people(size)}."
    )


def size_underused(size: int, room_count: int) -> str:
    return (
        f"Asunnossa on {rooms(room_count)} ja ruokakunnassasi on {people(size)}. Voit hakea, "
        "mutta suurempi ruokakunta voi saada etusijan."
    )


def household_missing() -> str:
    return "Lisää ruokakunnan jäsenet kohdassa Ruokakunta, jotta voimme arvioida asunnon koon."


# -- YLEIS-VANHENTUNUT-01 --------------------------------------------------


def application_valid_until(expires_at: dt.datetime) -> str:
    return f"Hakemuksesi on voimassa {date(expires_at)} asti."


def application_expired(expires_at: dt.datetime) -> str:
    return (
        f"Hakemuksesi vanheni {date(expires_at)}. Avaa muokkauslinkki ja vahvista tiedot, "
        "niin käsittelemme hakemuksen uudelleen."
    )


# -- API error messages ----------------------------------------------------
# Shown to the applicant, so they say what to do rather than what went wrong.


def unit_not_found() -> str:
    return "Asuntoa ei löytynyt. Se on voitu poistaa hausta."


def application_not_found() -> str:
    return "Hakemusta ei löytynyt. Tarkista muokkauslinkki tai aloita uusi hakemus."


def viewing_not_found() -> str:
    return "Näyttöaikaa ei löytynyt."


def viewing_full() -> str:
    return "Näyttö on täynnä. Valitse toinen näyttöaika."


def already_booked() -> str:
    return "Olet jo varannut paikan tähän näyttöön."


def unit_already_in_application() -> str:
    return "Asunto on jo hakemuksellasi."


def unit_not_in_application() -> str:
    return "Asunto ei ole hakemuksellasi."


def sale_unit_cannot_be_applied_for() -> str:
    return (
        "Myytävää asuntoa ei haeta hakemuksella. Varaa näyttöaika tai jätä tarjous asunnon sivulla."
    )


def offers_only_for_sale_units() -> str:
    return "Tarjouksen voi jättää vain myytävästä asunnosta."


def too_many_requests() -> str:
    return (
        "Hakemusta on muokattu liian monta kertaa lyhyessä ajassa. Odota hetki ja yritä uudelleen."
    )

"""Seed content that enriches the 8 properties and 48 units defined in ``seeds/data.py``.

Everything in this module is invented for the demo, exactly like ``seeds/data.py``:
descriptions, contact people, phone numbers and e-mail addresses do not refer to any real
person or business. The photographs are stock images pulled from Unsplash under the
Unsplash licence (free to use, attribution appreciated but not required); they are generic
interior, exterior and floor-plan photography reused across several listings and do **not**
depict the apartments, buildings or people described in this file. Photo credits name the
actual Unsplash photographer for the exact image referenced, verified against the live
Unsplash CDN before being written here.

This file only adds data. It does not touch ``seeds/data.py``, the ORM models, or any
migration, and it does not change the shape of the eight ``PropertySeed`` / 48 ``UnitSeed``
records already seeded elsewhere -- it is keyed off them by ``(property_name, unit_number)``.

Coordinate note: four of the eight properties in ``seeds/data.py`` carry lat/lng that drift
50-700 metres from the named street (checked against OpenStreetMap/Nominatim on 2026-09-02).
``PROPERTY_COORDINATES`` below holds corrected values for all eight so every pin sits on its
street and the map does not cluster. The largest correction is Suvelan aukio: "Kirstinkatu"
does not exist in Espoo's road register, only "Kirstintie" in the Kirstinharju part of
Suvela/Espoon keskus (postal area 02770) -- the coordinate below points at that street since
it is the closest real match for the fictional address in ``seeds/data.py``.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class UnitImage:
    url: str
    kind: str  # "valokuva" | "pohjapiirros"
    alt_fi: str
    credit: str
    sort_order: int


@dataclass(frozen=True, slots=True)
class UnitListing:
    room_layout_fi: str
    dwelling_type: str  # "kerrostalo" | "rivitalo" | "omakotitalo" | "luhtitalo"
    description_fi: str
    has_lift: bool
    has_sauna: bool
    has_balcony: bool
    pets_allowed: bool
    accessible: bool
    images: tuple[UnitImage, ...]
    maintenance_fee_eur: Decimal | None = None


@dataclass(frozen=True, slots=True)
class PropertyContact:
    name: str
    title_fi: str
    email: str
    phone: str
    photo_url: str


@dataclass(frozen=True, slots=True)
class PropertyCoordinates:
    lat: Decimal
    lng: Decimal


def _d(value: str) -> Decimal:
    return Decimal(value)


def _photo_url(photo_id: str) -> str:
    return f"https://images.unsplash.com/photo-{photo_id}?w=1200&q=80"


def _photo(photo_id: str, alt_fi: str, credit: str, sort_order: int) -> UnitImage:
    return UnitImage(
        url=_photo_url(photo_id),
        kind="valokuva",
        alt_fi=alt_fi,
        credit=credit,
        sort_order=sort_order,
    )


def _plan(photo_id: str, alt_fi: str, credit: str, sort_order: int) -> UnitImage:
    return UnitImage(
        url=_photo_url(photo_id),
        kind="pohjapiirros",
        alt_fi=alt_fi,
        credit=credit,
        sort_order=sort_order,
    )


# ---------------------------------------------------------------------------
# Image pool. Every id below returned HTTP 200 from images.unsplash.com when checked, and
# every photographer name was read directly off that photo's own unsplash.com/photos page
# (og:image + byline), not guessed from the id. Photos are reused across units on purpose --
# see the module docstring -- but never twice within the same unit.
# ---------------------------------------------------------------------------

_LIVING_KITCHEN: tuple[tuple[str, str, str], ...] = (
    (
        "1583847268964-b28dc8f51f92",
        "Valoisa olohuone, jossa on suuret ikkunat ja vaalea sisustus.",
        "Kuva: Minh Pham / Unsplash",
    ),
    (
        "1747336754870-ca7b10cc75f5",
        "Tyylikäs olohuone neutraaleilla sävyillä ja pehmeällä matolla.",
        "Kuva: Luis J. Corniel / Unsplash",
    ),
    (
        "1723748972084-4124765e0a55",
        "Kodikas olohuone, jossa on sohva ja avotakka.",
        "Kuva: Clay Banks / Unsplash",
    ),
    (
        "1772797583328-f83bc3f94f80",
        "Moderni olohuone puisin yksityiskohdin ja runsaalla luonnonvalolla.",
        "Kuva: Puscas Adryan / Unsplash",
    ),
    (
        "1522708323590-d24dbb6b0267",
        "Avara olohuone, josta on näkymä keittiöön.",
        "Kuva: Deborah Cortelazzi / Unsplash",
    ),
    (
        "1630699144641-72fa7a6b8aa1",
        "Valkoinen keittiö, jossa on tumma keittiösaareke.",
        "Kuva: Point3D Commercial Imaging Ltd. / Unsplash",
    ),
    (
        "1597497522150-2f50bffea452",
        "Keittiön hana ja työtaso lähikuvassa.",
        "Kuva: Filip Baotić / Unsplash",
    ),
    (
        "1755624222023-621f7718950b",
        "Moderni keittiö vihreällä välitilalaatoituksella.",
        "Kuva: Poojan Thanekar / Unsplash",
    ),
    (
        "1715985160053-d339e8b6eb94",
        "Keittiö, jossa jääkaappipakastin on sijoitettu työtason viereen.",
        "Kuva: Gerda Kauks / Unsplash",
    ),
)

_BEDROOM_BATHROOM: tuple[tuple[str, str, str], ...] = (
    (
        "1552858725-a19e7fcd3ac4",
        "Makuuhuone, jossa on sängyn vieressä lukulamppu.",
        "Kuva: Jp Valery / Unsplash",
    ),
    (
        "1499916078039-922301b0eb9b",
        "Makuuhuone, jonka nurkassa on nojatuoli ja viherkasveja.",
        "Kuva: Timothy Buck / Unsplash",
    ),
    (
        "1541004995602-b3e898709909",
        "Makuuhuone, jossa on suuri ikkuna ja siisti vuodesetti.",
        "Kuva: Devin Kleu / Unsplash",
    ),
    (
        "1631889993959-41b4e9c6e3c5",
        "Kylpyhuone, jossa on allas, peili ja amme.",
        "Kuva: Backbone / Unsplash",
    ),
    (
        "1650894622076-e09ab837c502",
        "Kylpyhuone, jossa on valkoinen allaskaappi ja peili.",
        "Kuva: Alona Gross / Unsplash",
    ),
)

_FLOORPLAN: tuple[tuple[str, str, str], ...] = (
    (
        "1786550860329-f813516e9705",
        "Havainnollinen pohjapiirros huonejaosta.",
        "Kuva: Brian Zajac / Unsplash",
    ),
    (
        "1735795798441-89cb505e1970",
        "Arkkitehdin pohjapiirustuksia pöydällä.",
        "Kuva: K O / Unsplash",
    ),
    (
        "1610650394144-a778795cf585",
        "Suunnittelupiirustus ja lyijykynä paperilla.",
        "Kuva: Soham Banerjee / Unsplash",
    ),
)

_EXTERIOR: tuple[tuple[str, str, str], ...] = (
    (
        "1638973140785-3b918e290682",
        "Kerrostalon julkisivu ja pääsisäänkäynti.",
        "Kuva: Jason Grant / Unsplash",
    ),
    (
        "1516501312919-d0cb0b7b60b8",
        "Asuinkerrostalon julkisivua kuvattuna kadulta.",
        "Kuva: Nate Watson / Unsplash",
    ),
    (
        "1565043589221-1a6fd9ae45c7",
        "Asuinrakennuksen sisäpihan puoleinen julkisivu.",
        "Kuva: Duncan Kidd / Unsplash",
    ),
    (
        "1781484966813-7a7dd4d305cd",
        "Moderni asuinrakennus iltavalaistuksessa.",
        "Kuva: Jordan Heinz / Unsplash",
    ),
)


def _images(exterior: int, main: int, secondary: int, plan: int) -> tuple[UnitImage, ...]:
    ext_id, ext_alt, ext_credit = _EXTERIOR[exterior]
    main_id, main_alt, main_credit = _LIVING_KITCHEN[main]
    sec_id, sec_alt, sec_credit = _BEDROOM_BATHROOM[secondary]
    plan_id, plan_alt, plan_credit = _FLOORPLAN[plan]
    return (
        _photo(ext_id, ext_alt, ext_credit, 1),
        _photo(main_id, main_alt, main_credit, 2),
        _photo(sec_id, sec_alt, sec_credit, 3),
        _plan(plan_id, plan_alt, plan_credit, 4),
    )


# ---------------------------------------------------------------------------
# Contact people, one per property. Portrait credits verified the same way as the unit pool.
# ---------------------------------------------------------------------------

PROPERTY_CONTACTS: dict[str, PropertyContact] = {
    "Kalliolan portti": PropertyContact(
        name="Antti Virtanen",
        title_fi="Vuokrausneuvoja",
        email="antti.virtanen@asuntohaku-demo.fi",
        phone="+358 40 512 3456",
        photo_url=_photo_url("1560250097-0b93528c311a"),  # LinkedIn Sales Solutions
    ),
    "Vallilan verstas": PropertyContact(
        name="Liisa Mäkinen",
        title_fi="Asuntosihteeri",
        email="liisa.makinen@asuntohaku-demo.fi",
        phone="+358 45 678 9012",
        photo_url=_photo_url("1627161683077-e34782c24d81"),  # Clay Elliot
    ),
    "Matinpuron rivi": PropertyContact(
        name="Juho Laine",
        title_fi="Vuokrausneuvoja",
        email="juho.laine@asuntohaku-demo.fi",
        phone="+358 50 234 5678",
        photo_url=_photo_url("1500648767791-00dcc994a43e"),  # Jurica Koletić
    ),
    "Suvelan aukio": PropertyContact(
        name="Anniina Korhonen",
        title_fi="Asumisoikeusneuvoja",
        email="anniina.korhonen@asuntohaku-demo.fi",
        phone="+358 44 789 1234",
        photo_url=_photo_url("1699899657680-421c2c2d5064"),  # Giorgio Trovato
    ),
    "Tikkurilan asemanseutu": PropertyContact(
        name="Markus Nieminen",
        title_fi="Vuokrausneuvoja",
        email="markus.nieminen@asuntohaku-demo.fi",
        phone="+358 40 345 6789",
        photo_url=_photo_url("1519085360753-af0119f7cbe7"),  # Ali Morshedlou
    ),
    "Myyrmäen tori": PropertyContact(
        name="Satu Hämäläinen",
        title_fi="Myyntineuvoja",
        email="satu.hamalainen@asuntohaku-demo.fi",
        phone="+358 50 987 6543",
        photo_url=_photo_url("1611432579699-484f7990b127"),  # alex starnes
    ),
    "Kalevan kaari": PropertyContact(
        name="Elina Salonen",
        title_fi="Asumisoikeusneuvoja",
        email="elina.salonen@asuntohaku-demo.fi",
        phone="+358 45 123 4567",
        photo_url=_photo_url("1573497019940-1c28c88b4f3e"),  # Christina @ wocintechchat.com
    ),
    "Hervannan piha": PropertyContact(
        name="Tuomas Rantanen",
        title_fi="Kiinteistöpäällikkö",
        email="tuomas.rantanen@asuntohaku-demo.fi",
        phone="+358 44 567 8901",
        photo_url=_photo_url("1629425733761-caae3b5f2e50"),  # Willian Souza
    ),
}


# ---------------------------------------------------------------------------
# Corrected coordinates. Geocoded against OpenStreetMap/Nominatim for the exact street named
# in seeds/data.py. See the module docstring for the Kirstinkatu/Kirstintie caveat.
# ---------------------------------------------------------------------------

PROPERTY_COORDINATES: dict[str, PropertyCoordinates] = {
    "Kalliolan portti": PropertyCoordinates(lat=_d("60.182800"), lng=_d("24.952450")),
    "Vallilan verstas": PropertyCoordinates(lat=_d("60.193730"), lng=_d("24.955870")),
    "Matinpuron rivi": PropertyCoordinates(lat=_d("60.158225"), lng=_d("24.739950")),
    "Suvelan aukio": PropertyCoordinates(lat=_d("60.201000"), lng=_d("24.666500")),
    "Tikkurilan asemanseutu": PropertyCoordinates(lat=_d("60.292890"), lng=_d("25.037110")),
    "Myyrmäen tori": PropertyCoordinates(lat=_d("60.263090"), lng=_d("24.852790")),
    "Kalevan kaari": PropertyCoordinates(lat=_d("61.495900"), lng=_d("23.804280")),
    "Hervannan piha": PropertyCoordinates(lat=_d("61.446240"), lng=_d("23.852500")),
}


# ---------------------------------------------------------------------------
# Per-unit listing content, keyed by (property name, unit number) exactly as spelled in
# seeds/data.py.
# ---------------------------------------------------------------------------

UNIT_LISTINGS: dict[tuple[str, str], UnitListing] = {
    # --- Kalliolan portti (Porthaninkatu 14, Helsinki, kerrostalo 2018) ---
    ("Kalliolan portti", "A 12"): UnitListing(
        room_layout_fi="1h + kk",
        dwelling_type="kerrostalo",
        description_fi=(
            "Yksiö sijaitsee kolmannessa kerroksessa vuonna 2018 valmistuneessa "
            "kerrostalossa Porthaninkadulla. Avokeittiö avautuu suoraan olohuoneeseen, "
            "ja parveke on rauhallisella sisäpihan puolella, poissa kadun äänistä. "
            "Taloyhtiössä on hissi sekä asukkaiden yhteinen sauna, jonka voi varata "
            "omaan käyttöön. Kallion kauppoihin, kahviloihin ja Hakaniemen "
            "metroasemalle on kävellen vain muutama minuutti. Asunto sopii hyvin "
            "yksin tai pariskuntana asuvalle, joka arvostaa keskeistä sijaintia ilman "
            "auton tarvetta."
        ),
        has_lift=True,
        has_sauna=True,
        has_balcony=True,
        pets_allowed=True,
        accessible=False,
        images=_images(exterior=0, main=0, secondary=3, plan=0),
    ),
    ("Kalliolan portti", "A 21"): UnitListing(
        room_layout_fi="2h + kk",
        dwelling_type="kerrostalo",
        description_fi=(
            "Kaksio neljännessä kerroksessa, jossa makuuhuone on erotettu "
            "olohuoneesta liukuovella - ratkaisu tekee tilasta joustavan sekä "
            "työskentelyyn että nukkumiseen. Ikkunat avautuvat kahteen suuntaan, "
            "joten valoa riittää aamusta iltaan. Keittiössä on astianpesukone ja "
            "hyvin tilaa aterioinnille. Metroasemalle kävelee kuudessa minuutissa, "
            "joten työmatkat Helsingin keskustaan tai Itäkeskukseen sujuvat ilman "
            "vaihtoja. Sopii erinomaisesti työssäkäyvälle parille tai etätyötä "
            "tekevälle, joka kaipaa oman nurkan kotiin."
        ),
        has_lift=True,
        has_sauna=False,
        has_balcony=False,
        pets_allowed=True,
        accessible=False,
        images=_images(exterior=0, main=1, secondary=0, plan=1),
    ),
    ("Kalliolan portti", "B 4"): UnitListing(
        room_layout_fi="2h + kk",
        dwelling_type="kerrostalo",
        description_fi=(
            "Katutason kaksio, jonka omalta terassilta on suora käynti pihalle - "
            "sisään pääsee siis kulkematta rappukäytävän kautta, mikä tekee "
            "asunnosta helposti saavutettavan myös lastenvaunujen tai pyörätuolin "
            "kanssa. Ratkaisu on omiaan myös koiranomistajalle, jolle lyhyt lenkki "
            "onnistuu suoraan kotiovelta. Keittiö on avoin olohuoneeseen ja tilaa on "
            "niin ruokailulle kuin oleskelullekin. Kallion vilkkaat kadut ja puistot "
            "ovat lähellä, mutta oma terassi tarjoaa rauhallisen hetken kotipihalla. "
            "Talossa on lisäksi hissi, joka palvelee muita kerroksia."
        ),
        has_lift=True,
        has_sauna=False,
        has_balcony=False,
        pets_allowed=True,
        accessible=True,
        images=_images(exterior=0, main=5, secondary=1, plan=2),
    ),
    ("Kalliolan portti", "B 17"): UnitListing(
        room_layout_fi="3h + k + khh",
        dwelling_type="kerrostalo",
        description_fi=(
            "Kolmio talon ylimmässä, viidennessä kerroksessa avautuu olohuoneen "
            "ikkunoista näkymä Kallion kirkolle asti. Kylpyhuone on remontoitu "
            "vuonna 2023, joten pinnat ja kalusteet ovat tuoreet. Asunnossa on myös "
            "erillinen kodinhoitohuone, johon mahtuvat pesukone ja kuivausteline "
            "pois keittiön tieltä. Erillinen keittiö rauhoittaa ruoanlaiton omaksi "
            "tilakseen olohuoneesta. Talon hissi kulkee kaikkiin kerroksiin, joten "
            "ylimmän kerroksen sijainti ei tuo arkeen lisävaivaa."
        ),
        has_lift=True,
        has_sauna=False,
        has_balcony=False,
        pets_allowed=True,
        accessible=False,
        images=_images(exterior=0, main=6, secondary=4, plan=0),
    ),
    ("Kalliolan portti", "C 15"): UnitListing(
        room_layout_fi="3h + k",
        dwelling_type="kerrostalo",
        description_fi=(
            "Kolmio neljännessä kerroksessa, jossa molemmat makuuhuoneet "
            "sijaitsevat pihan puolella - kaupungin äänet eivät kantaudu "
            "nukkumatiloihin asti. Keittiössä on tilaa ruokapöydälle kuudelle "
            "hengelle, mikä tekee siitä luontevan kokoontumispaikan perheelle tai "
            "kimppakämpän asukkaille. Olohuone on erillinen ja avautuu kadun "
            "suuntaan. Porthaninkadulta on lyhyt matka sekä Kallion että Hakaniemen "
            "palveluihin. Talossa on hissi ja asukassauna, joita moni tässä koossa "
            "asuva ruokakunta pitää arjen etuna."
        ),
        has_lift=True,
        has_sauna=True,
        has_balcony=False,
        pets_allowed=True,
        accessible=False,
        images=_images(exterior=0, main=2, secondary=2, plan=1),
    ),
    ("Kalliolan portti", "A 30"): UnitListing(
        room_layout_fi="2h + kk",
        dwelling_type="kerrostalo",
        description_fi=(
            "Myytävä kaksio kuudennessa eli ylimmässä kerroksessa. Lasitettu "
            "parveke avautuu lounaaseen, joten iltapäivän aurinko lämmittää sitä "
            "pitkälle iltaan. Keittiössä on kivitasot ja moderni ilme, joka sopii "
            "sekä arkikäyttöön että kutsuille. Taloyhtiöllä ei ole lainaa, mikä "
            "näkyy suoraan kuukausikuluissa. Sijainti Porthaninkadulla tarkoittaa "
            "lyhyttä matkaa Kallion palveluihin ja hyviä liikenneyhteyksiä ympäri "
            "kaupunkia."
        ),
        has_lift=True,
        has_sauna=False,
        has_balcony=True,
        pets_allowed=True,
        accessible=False,
        images=_images(exterior=0, main=3, secondary=3, plan=2),
        maintenance_fee_eur=_d("316.40"),
    ),
    ("Kalliolan portti", "B 22"): UnitListing(
        room_layout_fi="3h + k",
        dwelling_type="kerrostalo",
        description_fi=(
            "Myytävä kolmio, jonka läpitalon pohjaratkaisu tuo asuntoon valoa "
            "aamusta iltaan - toinen parveke avautuu aamuaurinkoon ja toinen "
            "iltapäivän puolelle. Taloyhtiö on teettänyt kuntoarvion keväällä 2026, "
            "joten ostaja saa ajantasaisen kuvan rakennuksen kunnosta. Keittiö ja "
            "olohuone ovat avarat, ja makuuhuoneet sijoittuvat rauhalliselle "
            "puolelle. Hissi ja asukassauna kuuluvat taloyhtiön palveluihin. Kallion "
            "kaupunginosa tarjoaa kävelymatkan päässä sekä ruokakaupat että "
            "ravintolat."
        ),
        has_lift=True,
        has_sauna=False,
        has_balcony=True,
        pets_allowed=True,
        accessible=False,
        images=_images(exterior=0, main=4, secondary=0, plan=0),
        maintenance_fee_eur=_d("399.60"),
    ),
    ("Kalliolan portti", "C 27"): UnitListing(
        room_layout_fi="1h + kk",
        dwelling_type="kerrostalo",
        description_fi=(
            "Myytävä yksiö talon ylimmässä kerroksessa. Parveke avautuu itään, "
            "joten aamuaurinko herättää huoneiston luontevasti. Pohjaratkaisu on "
            "tehokas eikä sisällä hukkaneliöitä, joten kolmekymmentäneljä neliötä "
            "riittää yllättävän hyvin sekä oleskeluun että työskentelyyn kotoa "
            "käsin. Talossa on hissi, joten ylin kerros ei ole arjessa haittana. "
            "Sijoittajalle tai ensiasunnon ostajalle kohde tarjoaa keskeisen "
            "sijainnin Kalliossa kohtuullisella neliöhinnalla."
        ),
        has_lift=True,
        has_sauna=False,
        has_balcony=True,
        pets_allowed=True,
        accessible=False,
        images=_images(exterior=0, main=1, secondary=1, plan=1),
        maintenance_fee_eur=_d("204.00"),
    ),
    ("Kalliolan portti", "B 9"): UnitListing(
        room_layout_fi="4h + k + s + kph",
        dwelling_type="kerrostalo",
        description_fi=(
            "Myytävä neljän huoneen asunto toisessa kerroksessa sopii isommalle "
            "ruokakunnalle. Asunnossa on oma sauna ja kaksi kylpyhuonetta, joten "
            "aamuruuhka ei ole ongelma useamman aikuisen taloudessa. Kaikki "
            "makuuhuoneet avautuvat rauhalliselle sisäpihalle, kun taas olohuone ja "
            "keittiö ovat kadun puolella. Talon hissi ja asukassauna täydentävät "
            "kokonaisuutta. Porthaninkadun sijainti tuo lähelle sekä Kallion "
            "palvelut että hyvät kulkuyhteydet keskustaan."
        ),
        has_lift=True,
        has_sauna=True,
        has_balcony=False,
        pets_allowed=True,
        accessible=False,
        images=_images(exterior=0, main=5, secondary=3, plan=2),
        maintenance_fee_eur=_d("489.60"),
    ),
    # --- Vallilan verstas (Sturenkatu 27, Helsinki, kerrostalo 1974) ---
    ("Vallilan verstas", "A 3"): UnitListing(
        room_layout_fi="1h + kk",
        dwelling_type="kerrostalo",
        description_fi=(
            "Yksiö ensimmäisessä kerroksessa, ikkunat avautuvat rauhalliselle "
            "sisäpihalle. Talossa on asukastupa yhteisiä tilaisuuksia varten sekä "
            "edullinen pyykkitupa, joka helpottaa arjen pesuhuoltoa. Avokeittiö on "
            "kompakti mutta toimiva, ja tilaa löytyy niin sängylle kuin "
            "työpisteellekin. Rakennus vuodelta 1974 on vanhaa Vallilaa "
            "parhaimmillaan: tiiliset julkisivut ja korkeat huonekorkeudet. "
            "Sturenkadulta on lyhyt matka sekä ratikkapysäkeille että Vallilan "
            "siirtolapuutarhaan kävelylenkille."
        ),
        has_lift=False,
        has_sauna=False,
        has_balcony=False,
        pets_allowed=True,
        accessible=False,
        images=_images(exterior=1, main=0, secondary=1, plan=1),
    ),
    ("Vallilan verstas", "A 14"): UnitListing(
        room_layout_fi="2h + kk",
        dwelling_type="kerrostalo",
        description_fi=(
            "Kaksio kolmannessa kerroksessa, jossa alkuperäinen parketti on "
            "säilynyt hyväkuntoisena vuosikymmenten varrella ja tuo huoneistoon "
            "lämpöä ja luonnetta. Parvekkeelta näkyy Vallilan siirtolapuutarhan "
            "värikkäät mökit ja puutarhat, mikä tekee aamukahvista oman pienen "
            "elämyksen. Avokeittiö on yhdistetty olohuoneeseen, ja makuuhuoneeseen "
            "mahtuu hyvin parisänky. Talossa on tarveharkintainen vuokra, joka "
            "näkyy suoraan kohtuullisena kuukausivuokrana. Sturenkadun varrelta "
            "pääsee ratikalla nopeasti sekä keskustaan että Pasilaan."
        ),
        has_lift=False,
        has_sauna=False,
        has_balcony=True,
        pets_allowed=True,
        accessible=False,
        images=_images(exterior=1, main=1, secondary=2, plan=2),
    ),
    ("Vallilan verstas", "B 6"): UnitListing(
        room_layout_fi="3h + k",
        dwelling_type="kerrostalo",
        description_fi=(
            "Kolmio sopii erinomaisesti kahden lapsen perheelle: molemmat "
            "makuuhuoneet ovat omia rauhoittumisen paikkoja, ja tilava eteinen "
            "jättää tilaa rattaille ja ulkovaatteille. Keittiö on erillinen "
            "olohuoneesta, joten ruoanlaiton hälinä ei häiritse muuta asumista. "
            "Koulu ja päiväkoti löytyvät saman korttelin sisältä, mikä lyhentää "
            "aamuisin lasten saattomatkan minuutteihin. Toisessa kerroksessa "
            "sijaitseva asunto on myös helppo kulkea ilman hissiä. Vallilan "
            "rauhallinen kerrostaloalue on suosittu juuri lapsiperheiden "
            "keskuudessa."
        ),
        has_lift=False,
        has_sauna=False,
        has_balcony=False,
        pets_allowed=True,
        accessible=False,
        images=_images(exterior=1, main=2, secondary=0, plan=0),
    ),
    ("Vallilan verstas", "B 19"): UnitListing(
        room_layout_fi="4h + k",
        dwelling_type="kerrostalo",
        description_fi=(
            "Neljän huoneen asunto sopii isolle ruokakunnalle tai useamman "
            "hengen jaetulle taloudelle. Keittiö on remontoitu vuonna 2021, joten "
            "kodinkoneet ja pinnat ovat nykyaikaiset vanhan talon puitteissa. "
            "Asunnossa on kaksi erillistä wc:tä, mikä helpottaa aamuruuhkaa, kun "
            "useampi lähtee liikkeelle samaan aikaan. Huoneet jakautuvat väljästi, "
            "ja olohuone toimii luontevana yhteisenä tilana. Neljännestä "
            "kerroksesta on hyvät näkymät Vallilan kattojen ylle, ja Sturenkadun "
            "ratikkapysäkille on lyhyt kävelymatka."
        ),
        has_lift=False,
        has_sauna=False,
        has_balcony=False,
        pets_allowed=True,
        accessible=False,
        images=_images(exterior=1, main=3, secondary=1, plan=1),
    ),
    ("Vallilan verstas", "C 2"): UnitListing(
        room_layout_fi="2h + kk",
        dwelling_type="kerrostalo",
        description_fi=(
            "Kaksio ensimmäisessä kerroksessa on suunniteltu esteettömäksi: "
            "sisäänkäynti on esteetön ja oviaukot leveät, joten asunto sopii hyvin "
            "myös liikkumisen apuvälineitä käyttävälle. Kylpyhuoneeseen mahtuu "
            "sekä pyykinpesukone että kuivausteline, mikä säästää tilaa muualta "
            "asunnosta. Avokeittiö yhdistyy olohuoneeseen, ja ikkunoista tulee "
            "mukavasti valoa. Ensimmäisen kerroksen sijainti tarkoittaa myös "
            "lyhyttä matkaa ulko-ovelle ilman portaita. Sturenkadun varsi tarjoaa "
            "lähipalvelut kävelymatkan päässä."
        ),
        has_lift=False,
        has_sauna=False,
        has_balcony=False,
        pets_allowed=True,
        accessible=True,
        images=_images(exterior=1, main=6, secondary=4, plan=2),
    ),
    ("Vallilan verstas", "C 23"): UnitListing(
        room_layout_fi="3h + k",
        dwelling_type="kerrostalo",
        description_fi=(
            "Kolmio talon ylimmässä, viidennessä kerroksessa on tilava ja "
            "valoisa: olohuone antaa hyvin tilaa sekä oleskelulle että "
            "ruokailulle. Makuuhuoneet sijaitsevat hiljaisella puolella pihaan "
            "päin, joten yöunet eivät häiriinny kadun äänistä. Taloyhtiössä on "
            "kattosauna, jonka voi varata asukkaiden yhteiskäyttöön - kätevä etu, "
            "kun asunnossa itsessään ei ole omaa saunaa. Rakennus vuodelta 1974 on "
            "tyypillistä vahvarakenteista Vallilan kerrostaloa. Sturenkadulta "
            "pääsee ratikalla ja bussilla nopeasti sekä keskustaan että Pasilan "
            "asemalle."
        ),
        has_lift=False,
        has_sauna=False,
        has_balcony=False,
        pets_allowed=True,
        accessible=False,
        images=_images(exterior=1, main=7, secondary=2, plan=0),
    ),
    # --- Matinpuron rivi (Matinkatu 9, Espoo, rivitalo 2021) ---
    ("Matinpuron rivi", "1"): UnitListing(
        room_layout_fi="2h + kk",
        dwelling_type="rivitalo",
        description_fi=(
            "Rivitalokaksio omalla pihalla sopii hyvin sekä pariskunnalle että "
            "yksin asuvalle, joka kaipaa maanläheistä asumista ilman kerrostalon "
            "yhteistiloja. Lattialämmitys ja ilmalämpöpumppu pitävät huoneiston "
            "lämpötilan tasaisena ympäri vuoden ja säästävät samalla "
            "lämmityskuluissa. Autokatospaikka sisältyy vuokraan, joten talvella "
            "ei tarvitse harjata lunta auton katolta. Talo on valmistunut vuonna "
            "2021, joten pinnat ja tekniikka ovat vielä täysin tuoreet. Matinkylän "
            "metroasemalle ja palveluihin on lyhyt matka, mikä tekee arjesta "
            "sujuvaa ilman omaa autoakin."
        ),
        has_lift=False,
        has_sauna=False,
        has_balcony=False,
        pets_allowed=True,
        accessible=False,
        images=_images(exterior=2, main=5, secondary=0, plan=1),
    ),
    ("Matinpuron rivi", "3"): UnitListing(
        room_layout_fi="3h + k",
        dwelling_type="rivitalo",
        description_fi=(
            "Kolme huonetta jakautuu kahteen kerrokseen: yläkerrassa on kaksi "
            "omaa makuuhuonetta, alakerrassa avara olohuone, josta pääsee suoraan "
            "terassille. Ratkaisu sopii hyvin perheelle, jossa lapset ja aikuiset "
            "kaipaavat omaa tilaa saman katon alla. Terassilta avautuu näkymä "
            "rivitalon yhteiselle pihalle, ja iltaa voi viettää ulkona ilman "
            "naapureiden vilkasta katsetta. Talo on rakennettu 2021, joten "
            "materiaalit ja eristys vastaavat nykypäivän vaatimuksia. Matinkadulta "
            "on hyvät kulkuyhteydet sekä Matinkylän metroasemalle että "
            "Länsiväylälle."
        ),
        has_lift=False,
        has_sauna=False,
        has_balcony=False,
        pets_allowed=True,
        accessible=False,
        images=_images(exterior=2, main=2, secondary=1, plan=2),
    ),
    ("Matinpuron rivi", "5"): UnitListing(
        room_layout_fi="3h + k",
        dwelling_type="rivitalo",
        description_fi=(
            "Päätyasunnossa on ikkunat kolmeen suuntaan, joten valoa riittää "
            "huoneistossa läpi päivän. Pihan puolella on aidattu leikkialue, joka "
            "tekee asunnosta erityisen sopivan pienten lasten perheelle - lapset "
            "voivat leikkiä turvallisesti ikkunoiden näköetäisyydellä. Kolme "
            "huonetta antaa tilaa sekä yhteiselle olohuoneelle että omille "
            "makuuhuoneille. Rakennusvuosi 2021 näkyy energiatehokkaassa "
            "lämmityksessä ja tiiviissä rakenteissa. Matinkylän palvelut ja koulut "
            "ovat kävelymatkan päässä."
        ),
        has_lift=False,
        has_sauna=False,
        has_balcony=False,
        pets_allowed=True,
        accessible=False,
        images=_images(exterior=2, main=4, secondary=2, plan=0),
    ),
    ("Matinpuron rivi", "7"): UnitListing(
        room_layout_fi="4h + k + s + khh",
        dwelling_type="rivitalo",
        description_fi=(
            "Perheasunto tarjoaa neljä huonetta, erillisen kodinhoitohuoneen ja "
            "oman saunan - harvinaisen kattava kokonaisuus vuokra-asunnoksi. "
            "Kodinhoitohuone pitää pyykit ja ulkovarusteet järjestyksessä erillään "
            "muusta asumisesta. Sauna mahdollistaa rauhoittumisen omassa rauhassa "
            "ilman taloyhtiön varauslistoja. Matinkylän metroasemalle kävelee noin "
            "kymmenessä minuutissa, joten työmatka keskustaan sujuu ilman autoa. "
            "Talo sopii erinomaisesti isommalle perheelle, joka arvostaa "
            "rivitaloasumisen tilavuutta ja omaa pihaa."
        ),
        has_lift=False,
        has_sauna=True,
        has_balcony=False,
        pets_allowed=True,
        accessible=False,
        images=_images(exterior=2, main=8, secondary=3, plan=1),
    ),
    ("Matinpuron rivi", "9"): UnitListing(
        room_layout_fi="2h + kk",
        dwelling_type="rivitalo",
        description_fi=(
            "Kaksio, jonka keittiö on varustettu astianpesukoneella ja "
            "induktioliedellä - arjen ruoanlaitto sujuu ilman turhaa säätöä. "
            "Asunnossa on lisäksi oma varasto, johon mahtuvat esimerkiksi "
            "polkupyörät ja kausivarusteet pois asuintiloista. Terassi avautuu "
            "etelään, joten aurinko paistaa sille suurimman osan päivästä. "
            "Rivitalo valmistui 2021, joten tekniikka ja pinnat ovat uudet. "
            "Matinkadun sijainti tarjoaa rauhallisen asuinympäristön, mutta silti "
            "lyhyen matkan Matinkylän palveluihin."
        ),
        has_lift=False,
        has_sauna=False,
        has_balcony=False,
        pets_allowed=True,
        accessible=False,
        images=_images(exterior=2, main=5, secondary=4, plan=2),
    ),
    # --- Suvelan aukio (Kirstinkatu 12, Espoo, kerrostalo 2009) ---
    ("Suvelan aukio", "A 5"): UnitListing(
        room_layout_fi="2h + kk + s",
        dwelling_type="kerrostalo",
        description_fi=(
            "Asumisoikeuskaksio, jossa on oma sauna - harvinainen etu tämän "
            "kokoluokan asunnossa. Lasitettu parveke pidentää ulkoilukautta "
            "keväästä pitkälle syksyyn ja suojaa samalla tuulelta. Käyttövastike "
            "sisältää veden ja taloyhtiön laajakaistan, joten kuukausikulut "
            "pysyvät ennakoitavina. Talo on valmistunut 2009 ja sijaitsee "
            "Kirstinharjun alueella, jossa on paljon vihreää ja rauhallisia "
            "kävelyreittejä. Asumisoikeusjärjestelmä sopii hyvin sille, joka "
            "haluaa vakautta ilman omistusasunnon koko taloudellista sitoumusta."
        ),
        has_lift=True,
        has_sauna=True,
        has_balcony=True,
        pets_allowed=True,
        accessible=False,
        images=_images(exterior=3, main=0, secondary=4, plan=0),
    ),
    ("Suvelan aukio", "A 18"): UnitListing(
        room_layout_fi="3h + k",
        dwelling_type="kerrostalo",
        description_fi=(
            "Kolmiossa keittiö ja olohuone muodostavat yhtenäisen, avaran "
            "tilan, joka toimii hyvin sekä arkena että vieraita "
            "vastaanotettaessa. Molemmat makuuhuoneet sijaitsevat rauhallisella "
            "puolella, poissa taloyhtiön pääsisäänkäynnin vilskeestä. Neljännestä "
            "kerroksesta avautuu näkymä yli lähialueen kattojen. Rakennus on osa "
            "2009 valmistunutta asumisoikeuskohdetta, jossa huoltokulut on "
            "suunniteltu pitkäjänteisesti. Espoon keskuksen palvelut ja "
            "juna-asema ovat kohtuullisen matkan päässä."
        ),
        has_lift=True,
        has_sauna=False,
        has_balcony=False,
        pets_allowed=True,
        accessible=False,
        images=_images(exterior=3, main=1, secondary=2, plan=1),
    ),
    ("Suvelan aukio", "B 7"): UnitListing(
        room_layout_fi="2h + kk",
        dwelling_type="kerrostalo",
        description_fi=(
            "Kaksio ensimmäisessä kerroksessa, josta pääsee terassin kautta "
            "suoraan omalle pihan osalle. Sisäänkäynti on esteetön, ja talon "
            "hissi vie kätevästi kellarikerroksen varastoihin, vaikka asunto "
            "itsessään sijaitsee maan tasalla. Avokeittiö on yhdistetty "
            "olohuoneeseen, ja tilaa riittää niin sohvalle kuin ruokapöydällekin. "
            "Ratkaisu sopii hyvin liikkumisesta apua tarvitsevalle tai "
            "lapsiperheelle, jolle rattaiden kanssa kulkeminen on arkea. Suvelan "
            "alue tarjoaa rauhallisen ympäristön lähellä Espoon keskuksen "
            "palveluita."
        ),
        has_lift=True,
        has_sauna=False,
        has_balcony=False,
        pets_allowed=True,
        accessible=True,
        images=_images(exterior=3, main=5, secondary=3, plan=2),
    ),
    ("Suvelan aukio", "B 16"): UnitListing(
        room_layout_fi="4h + k + s + kph",
        dwelling_type="kerrostalo",
        description_fi=(
            "Neljän huoneen asumisoikeusasunto tarjoaa tilaa isommalle "
            "ruokakunnalle: kaksi kylpyhuonetta, joista toisessa on sauna, "
            "helpottavat aamuja kun useampi valmistautuu samaan aikaan lähtöön. "
            "Huoneet jakautuvat väljästi ja olohuone on kooltaan reilu. "
            "Taloyhtiön pihalla on yhteinen grillikatos, joka kutsuu naapureita "
            "yhteisiin kesäiltoihin. Rakennus valmistui 2009 ja on pysynyt "
            "hyväkuntoisena säännöllisen huollon ansiosta. Kirstinharjun alue on "
            "suosittu perheiden keskuudessa juuri väljyytensä ja vehreytensä "
            "vuoksi."
        ),
        has_lift=True,
        has_sauna=True,
        has_balcony=False,
        pets_allowed=True,
        accessible=False,
        images=_images(exterior=3, main=6, secondary=0, plan=0),
    ),
    ("Suvelan aukio", "C 21"): UnitListing(
        room_layout_fi="3h + k",
        dwelling_type="kerrostalo",
        description_fi=(
            "Ylimmän kerroksen kolmiosta avautuu näkymä lähimetsän suuntaan, "
            "mikä tuo asuntoon rauhallisen tunnelman keskellä Espoota. Yksi "
            "makuuhuoneista on pienempi ja sopii erinomaisesti työhuoneeksi tai "
            "lastenhuoneeksi - joustavuus, jota moni etätyötä tekevä arvostaa. "
            "Keittiö ja olohuone ovat erilliset, mikä rauhoittaa molemmat tilat "
            "omaan käyttötarkoitukseensa. Talo on osa 2009 rakennettua "
            "asumisoikeuskohdetta Kirstinharjussa. Espoon keskuksen "
            "juna-asemalle ja palveluihin pääsee kohtuullisessa ajassa."
        ),
        has_lift=True,
        has_sauna=False,
        has_balcony=False,
        pets_allowed=True,
        accessible=False,
        images=_images(exterior=3, main=2, secondary=1, plan=1),
    ),
    # --- Tikkurilan asemanseutu (Kielotie 20, Vantaa, kerrostalo 1988) ---
    ("Tikkurilan asemanseutu", "A 7"): UnitListing(
        room_layout_fi="1h + kk",
        dwelling_type="kerrostalo",
        description_fi=(
            "Yksiö sijaitsee aivan juna-aseman vieressä, joten lentokentälle "
            "pääsee kehäradalla vaihtamatta ja Helsingin keskustaan muutamassa "
            "minuutissa. Talossa on hissi sekä valvottu pyöräkellari, joka tuo "
            "turvaa pyörän säilytykseen. Avokeittiö on kompakti mutta toimiva "
            "pienelle taloudelle. Rakennus vuodelta 1988 on tyypillistä "
            "Tikkurilan asemanseudun kerrostaloa, jonka huoltoyhtiö tuntee talon "
            "historian hyvin. Sijainti sopii erinomaisesti työmatkalaiselle, joka "
            "arvostaa nopeita julkisen liikenteen yhteyksiä."
        ),
        has_lift=True,
        has_sauna=False,
        has_balcony=False,
        pets_allowed=True,
        accessible=False,
        images=_images(exterior=1, main=5, secondary=3, plan=2),
    ),
    ("Tikkurilan asemanseutu", "A 22"): UnitListing(
        room_layout_fi="2h + kk",
        dwelling_type="kerrostalo",
        description_fi=(
            "Kaksio viidennessä kerroksessa, jonka parveke avautuu länteen - "
            "ilta-aurinko lämmittää parveketta pitkälle kesäiltaan asti. "
            "Keittiössä on tilaa ruokapöydälle, ja asunnossa on lisäksi iso "
            "vaatehuone, joka helpottaa säilytystilan puutetta monessa muussa "
            "saman kokoluokan asunnossa. Talo sijaitsee kävelymatkan päässä "
            "Tikkurilan asemasta ja sen palveluista. Rakennus on peruskorjattu "
            "vuosien varrella hyvässä huollossa. Sopii hyvin pariskunnalle tai "
            "yksin asuvalle, joka arvostaa säilytystilaa ja hyviä "
            "liikenneyhteyksiä."
        ),
        has_lift=True,
        has_sauna=False,
        has_balcony=True,
        pets_allowed=True,
        accessible=False,
        images=_images(exterior=1, main=3, secondary=0, plan=0),
    ),
    ("Tikkurilan asemanseutu", "B 3"): UnitListing(
        room_layout_fi="3h + k",
        dwelling_type="kerrostalo",
        description_fi=(
            "Kolmion pohjaratkaisu on toimiva pienelle perheelle: olohuone ja "
            "keittiö ovat avarat, ja molemmat makuuhuoneet antavat omaa tilaa "
            "niin vanhemmille kuin lapsille. Päiväkoti, kirjasto ja uimahalli "
            "löytyvät kaikki kävelymatkan päästä, mikä tekee arjen aikatauluista "
            "helposti hallittavia ilman autoa. Ensimmäisen kerroksen sijainti "
            "tarkoittaa lyhyttä matkaa ulko-ovelle. Talo on rakennettu 1988 ja "
            "sijaitsee aivan Tikkurilan asemanseudun palveluiden äärellä. "
            "Kehärata ja lähijunat vievät nopeasti sekä Helsinkiin että "
            "lentokentälle."
        ),
        has_lift=True,
        has_sauna=False,
        has_balcony=False,
        pets_allowed=True,
        accessible=False,
        images=_images(exterior=1, main=1, secondary=1, plan=1),
    ),
    ("Tikkurilan asemanseutu", "B 14"): UnitListing(
        room_layout_fi="4h + k",
        dwelling_type="kerrostalo",
        description_fi=(
            "Neljän huoneen asunto sopii ruokakunnalle, jossa on useampi lapsi: "
            "kolme erillistä makuuhuonetta antaa jokaiselle oman nurkan, ja "
            "erillinen keittiö pitää ruoanlaiton omana tilanaan. Olohuone toimii "
            "perheen yhteisenä kokoontumispaikkana iltaisin. Kolmannesta "
            "kerroksesta on hyvät näkymät Tikkurilan kattojen yli. Talo on "
            "rakennettu 1988 ja sijaitsee kävelymatkan päässä asemasta, "
            "kouluista ja päiväkodeista. Alue on tunnettu hyvistä palveluistaan "
            "ja toimivista liikenneyhteyksistään."
        ),
        has_lift=True,
        has_sauna=False,
        has_balcony=False,
        pets_allowed=True,
        accessible=False,
        images=_images(exterior=1, main=7, secondary=2, plan=2),
    ),
    ("Tikkurilan asemanseutu", "C 6"): UnitListing(
        room_layout_fi="2h + kk",
        dwelling_type="kerrostalo",
        description_fi=(
            "Kaksio sisäpihan puolella on poikkeuksellisen hiljainen, sillä "
            "kadun äänet eivät kantaudu ikkunoihin asti. Kylpyhuone on uusittu "
            "vuonna 2020, ja koko taloon on tehty putkiremontti, joten "
            "talotekniikka on ajan tasalla. Avokeittiö yhdistyy olohuoneeseen, ja "
            "tilaa riittää sekä oleskelulle että ruokailulle. Toinen kerros on "
            "helppo kulkea myös ilman hissiä. Tikkurilan asema ja palvelut ovat "
            "lyhyen kävelymatkan päässä."
        ),
        has_lift=True,
        has_sauna=False,
        has_balcony=False,
        pets_allowed=True,
        accessible=False,
        images=_images(exterior=1, main=6, secondary=4, plan=0),
    ),
    ("Tikkurilan asemanseutu", "C 27"): UnitListing(
        room_layout_fi="3h + k",
        dwelling_type="kerrostalo",
        description_fi=(
            "Kolmio talon ylimmässä, kuudennessa kerroksessa tarjoaa "
            "olohuoneesta näkymän radan yli aina Tikkurilanjoelle asti. "
            "Taloyhtiössä on yhteinen kattoterassi, jolta näkymät ovat "
            "vieläkin avarammat - kätevä lisä, kun oma parveke ei ole tarpeeksi. "
            "Makuuhuoneet sijaitsevat rauhallisella puolella pihaan päin. "
            "Rakennus vuodelta 1988 on osa vilkasta mutta viihtyisää Tikkurilan "
            "asemanseutua. Juna-asemalle ja kehäradalle on vain muutaman "
            "minuutin kävelymatka."
        ),
        has_lift=True,
        has_sauna=False,
        has_balcony=False,
        pets_allowed=True,
        accessible=False,
        images=_images(exterior=1, main=0, secondary=3, plan=1),
    ),
    # --- Myyrmäen tori (Liesitori 3, Vantaa, kerrostalo 2015) ---
    ("Myyrmäen tori", "A 9"): UnitListing(
        room_layout_fi="2h + kk",
        dwelling_type="kerrostalo",
        description_fi=(
            "Kaksio sijaitsee aivan Myyrmäen torin laidalla, jonka ympärillä "
            "ovat sekä kauppa, apteekki että juna-asema - arjen asiat hoituvat "
            "kävellen ilman erillisiä automatkoja. Lasitettu parveke pidentää "
            "ulkoiluaikaa ja suojaa säältä ympäri vuoden. Avokeittiö on "
            "yhdistetty olohuoneeseen, mikä tekee tilasta avaran vaikutelman "
            "kompaktista koosta huolimatta. Talo on valmistunut 2015, joten "
            "rakenteet ja tekniikka ovat vielä tuoreet. Sijainti sopii hyvin "
            "työssäkäyvälle, joka arvostaa lyhyttä etäisyyttä juna-asemalle."
        ),
        has_lift=True,
        has_sauna=False,
        has_balcony=True,
        pets_allowed=True,
        accessible=False,
        images=_images(exterior=2, main=0, secondary=0, plan=2),
    ),
    ("Myyrmäen tori", "A 24"): UnitListing(
        room_layout_fi="3h + k + s",
        dwelling_type="kerrostalo",
        description_fi=(
            "Kolmio kuudennessa kerroksessa tarjoaa näkymän Vantaanjoelle asti "
            "- ilta-auringon lasku joen ylle näkyy parhaiten juuri tästä "
            "kerroksesta. Asunnossa on oma sauna, mikä on harvinainen etu "
            "vuokra-asunnossa tässä kokoluokassa. Lasitettu parveke laajentaa "
            "oleskelutilaa ulos säällä kuin säällä. Keittiö ja olohuone ovat "
            "avarat, ja makuuhuoneet sijaitsevat rauhallisella puolella. "
            "Myyrmäen torin palvelut ja juna-asema ovat lyhyen kävelymatkan "
            "päässä."
        ),
        has_lift=True,
        has_sauna=True,
        has_balcony=True,
        pets_allowed=True,
        accessible=False,
        images=_images(exterior=2, main=4, secondary=4, plan=0),
    ),
    ("Myyrmäen tori", "B 2"): UnitListing(
        room_layout_fi="1h + kk",
        dwelling_type="kerrostalo",
        description_fi=(
            "Yksiö ensimmäisessä kerroksessa, jossa iso ikkuna tuo huoneistoon "
            "runsaasti luonnonvaloa. Keittiönurkkaus on suunniteltu tehokkaaksi: "
            "kaikki tarvittava mahtuu pieneen tilaan ilman ahtauden tuntua. "
            "Sisäänkäynnin vieressä sijaitseva oma varasto tarjoaa lisätilaa "
            "esimerkiksi polkupyörälle tai kausivarusteille. Talo on rakennettu "
            "2015 ja sijaitsee kävelymatkan päässä Myyrmäen torista ja "
            "juna-asemasta. Sopii hyvin opiskelijalle tai yksin asuvalle, joka "
            "arvostaa keskeistä sijaintia edulliseen hintaan."
        ),
        has_lift=True,
        has_sauna=False,
        has_balcony=False,
        pets_allowed=True,
        accessible=False,
        images=_images(exterior=2, main=6, secondary=1, plan=1),
    ),
    ("Myyrmäen tori", "B 12"): UnitListing(
        room_layout_fi="2h + kk",
        dwelling_type="kerrostalo",
        description_fi=(
            "Kaksio, jonka makuuhuoneeseen mahtuu hyvin parisänky sekä "
            "työpöytä etätöitä varten. Taloyhtiössä on oma kuntosali ja kaksi "
            "saunaosastoa, jotka ovat asukkaiden varattavissa - mukava lisä "
            "arkeen ilman erillistä kuntosalijäsenyyttä. Avokeittiö on "
            "yhdistetty olohuoneeseen ja tilaa riittää myös ruokailulle. "
            "Rakennus vuodelta 2015 sijaitsee aivan Myyrmäen torin kupeessa. "
            "Juna-asemalle ja torin palveluihin on vain muutaman minuutin "
            "kävelymatka."
        ),
        has_lift=True,
        has_sauna=False,
        has_balcony=False,
        pets_allowed=True,
        accessible=False,
        images=_images(exterior=2, main=1, secondary=2, plan=2),
    ),
    ("Myyrmäen tori", "A 31"): UnitListing(
        room_layout_fi="2h + kk",
        dwelling_type="kerrostalo",
        description_fi=(
            "Myytävä kaksio talon ylimmässä, seitsemännessä kerroksessa. "
            "Lasitettu parveke avautuu lounaaseen, joten iltapäivät ja illat "
            "parvekkeella ovat aurinkoisia suuren osan vuodesta. Olohuone on "
            "avara ja yhdistyy keittiöön luontevasti. Hissi tuo asunnon ovelle "
            "asti, joten ylin kerros ei tarkoita rappusten kiipeämistä. "
            "Myyrmäen torin palvelut ja juna-asema ovat kävelymatkan päässä, "
            "mikä tekee kohteesta toimivan sekä omistusasunnoksi että "
            "sijoitukseksi."
        ),
        has_lift=True,
        has_sauna=False,
        has_balcony=True,
        pets_allowed=True,
        accessible=False,
        images=_images(exterior=2, main=3, secondary=3, plan=0),
        maintenance_fee_eur=_d("307.40"),
    ),
    ("Myyrmäen tori", "B 20"): UnitListing(
        room_layout_fi="3h + k + s",
        dwelling_type="kerrostalo",
        description_fi=(
            "Myytävä kolmio, jossa on oma sauna ja kaksi parveketta - toinen "
            "aamuauringolle, toinen iltapäivän valolle. Taloyhtiön "
            "lainaosuuden voi maksaa pois kerralla kaupanteon yhteydessä, mikä "
            "keventää tulevia yhtiövastikkeita. Keittiö ja olohuone ovat "
            "yhtenäinen, avara kokonaisuus. Makuuhuoneet sijaitsevat "
            "rauhallisella puolella taloa. Myyrmäen torin sijainti tarjoaa "
            "hyvät palvelut ja junayhteydet niin Helsinkiin kuin Tikkurilaankin."
        ),
        has_lift=True,
        has_sauna=True,
        has_balcony=True,
        pets_allowed=True,
        accessible=False,
        images=_images(exterior=2, main=5, secondary=0, plan=1),
        maintenance_fee_eur=_d("367.50"),
    ),
    ("Myyrmäen tori", "C 5"): UnitListing(
        room_layout_fi="1h + kk",
        dwelling_type="kerrostalo",
        description_fi=(
            "Myytävä yksiö sopii sekä ensiasunnon ostajalle että sijoittajalle. "
            "Alueen vuokra-asuntokanta on kysyttyä erityisesti opiskelijoiden "
            "keskuudessa, mikä tekee kohteesta houkuttelevan myös vuokrattavaksi. "
            "Avokeittiö ja olohuone muodostavat yhtenäisen, valoisan tilan. Talo "
            "on rakennettu 2015, joten kunnossapitokulut ovat vielä maltilliset. "
            "Myyrmäen juna-asemalle ja torin palveluihin on lyhyt kävelymatka."
        ),
        has_lift=True,
        has_sauna=False,
        has_balcony=False,
        pets_allowed=True,
        accessible=False,
        images=_images(exterior=2, main=0, secondary=4, plan=2),
        maintenance_fee_eur=_d("211.70"),
    ),
    ("Myyrmäen tori", "A 14"): UnitListing(
        room_layout_fi="4h + k + s",
        dwelling_type="kerrostalo",
        description_fi=(
            "Myytävä neljän huoneen asunto tarjoaa tilaa isommalle perheelle: "
            "oma sauna ja lasitettu parveke tekevät arjesta mukavan sekä "
            "sisällä että ulkona. Taloyhtiöön on tehty julkisivuremontti "
            "vuonna 2024, joten rakennuksen ulkokuori on tuore ja huoltovapaa "
            "lähivuosiksi. Huoneet jakautuvat väljästi, ja olohuone toimii "
            "perheen yhteisenä tilana. Neljäs kerros tarjoaa hyvät näkymät "
            "Myyrmäen ylle. Torin palvelut ja juna-asema ovat kävelymatkan "
            "päässä."
        ),
        has_lift=True,
        has_sauna=True,
        has_balcony=True,
        pets_allowed=True,
        accessible=False,
        images=_images(exterior=2, main=8, secondary=1, plan=0),
        maintenance_fee_eur=_d("432.40"),
    ),
    # --- Kalevan kaari (Sammonkatu 44, Tampere, kerrostalo 2012) ---
    ("Kalevan kaari", "A 4"): UnitListing(
        room_layout_fi="2h + kk",
        dwelling_type="kerrostalo",
        description_fi=(
            "Asumisoikeuskaksio, jossa on oma piha-alue ja lisäksi erillinen "
            "varasto tavaroiden säilytykseen. Kalevan kirkolle ja uimahallille "
            "on lyhyt kävelymatka, mikä tekee arki-illoista helposti aktiivisia "
            "ilman pitkiä siirtymiä. Avokeittiö yhdistyy olohuoneeseen "
            "luontevasti. Talo on valmistunut 2012 ja sijaitsee Sammonkadun "
            "varrella, jota pitkin kulkee myös raitiotie. Sopii hyvin "
            "pariskunnalle tai yksin asuvalle, joka arvostaa asumisoikeuden "
            "tuomaa vakautta."
        ),
        has_lift=True,
        has_sauna=False,
        has_balcony=False,
        pets_allowed=True,
        accessible=False,
        images=_images(exterior=3, main=1, secondary=3, plan=1),
    ),
    ("Kalevan kaari", "A 17"): UnitListing(
        room_layout_fi="3h + k + s",
        dwelling_type="kerrostalo",
        description_fi=(
            "Kolmiossa on oma sauna ja lasitettu parveke - yhdistelmä, joka "
            "tuo lisäarvoa arkeen ympäri vuoden. Keittiössä on astianpesukone ja "
            "erillinen ruokailutila, joka rauhoittaa aterioinnin omaksi "
            "hetkekseen. Kolmannesta kerroksesta avautuu näkymä Sammonkadun "
            "puistoiselle katukuvalle. Rakennus on osa 2012 valmistunutta "
            "asumisoikeuskohdetta Kalevassa. Ratikkalinja kulkee talon editse, "
            "joten keskustaan pääsee nopeasti ilman omaa autoa."
        ),
        has_lift=True,
        has_sauna=True,
        has_balcony=True,
        pets_allowed=True,
        accessible=False,
        images=_images(exterior=3, main=7, secondary=4, plan=2),
    ),
    ("Kalevan kaari", "B 8"): UnitListing(
        room_layout_fi="1h + kk",
        dwelling_type="kerrostalo",
        description_fi=(
            "Yksiö, jonka ikkunat avautuvat puistoon - vehreä näkymä tuo rauhaa "
            "myös keskellä kaupunkia. Käyttövastike sisältää sekä veden että "
            "taloyhtiön laajakaistan, joten kuukausikulut ovat helposti "
            "ennakoitavissa. Avokeittiö on kompakti mutta toimiva. Talo "
            "sijaitsee Sammonkadulla, jota pitkin kulkee Tampereen raitiotie "
            "suoraan keskustaan. Sopii hyvin opiskelijalle tai yksin asuvalle, "
            "joka arvostaa asumisoikeuden joustavuutta."
        ),
        has_lift=True,
        has_sauna=False,
        has_balcony=False,
        pets_allowed=True,
        accessible=False,
        images=_images(exterior=3, main=0, secondary=2, plan=0),
    ),
    ("Kalevan kaari", "B 19"): UnitListing(
        room_layout_fi="4h + k + kph",
        dwelling_type="kerrostalo",
        description_fi=(
            "Neljän huoneen asunto tarjoaa runsaasti tilaa: kaksi kylpyhuonetta "
            "helpottaa aamuja isommassa taloudessa, ja iso eteinen jättää tilaa "
            "ulkovaatteille ja kengille. Huoneet jakautuvat väljästi ympäri "
            "asuntoa, ja olohuone on perheen luonteva kokoontumispaikka. "
            "Ratikkapysäkki sijaitsee aivan talon edessä, joten matka Tampereen "
            "keskustaan tai Hervantaan sujuu ilman vaihtoja. Rakennus on "
            "valmistunut 2012 ja osa arvostettua asumisoikeuskohdetta Kalevassa."
        ),
        has_lift=True,
        has_sauna=False,
        has_balcony=False,
        pets_allowed=True,
        accessible=False,
        images=_images(exterior=3, main=6, secondary=1, plan=1),
    ),
    # --- Hervannan piha (Insinöörinkatu 60, Tampere, kerrostalo 2019) ---
    ("Hervannan piha", "A 2"): UnitListing(
        room_layout_fi="1h + kk",
        dwelling_type="kerrostalo",
        description_fi=(
            "Yksiö sijaitsee kävelymatkan päässä yliopiston kampuksesta, mikä "
            "tekee siitä suositun valinnan opiskelijalle. Keittiö on kalustettu "
            "valmiiksi, joten muutto sujuu ilman suuria hankintoja. Oma parveke "
            "tarjoaa ulkoilmahetken myös kiireisimpinä opiskelupäivinä. "
            "Ratikalla keskustaan pääsee noin kahdessakymmenessä minuutissa. "
            "Talo on valmistunut 2019, joten rakenteet ja tekniikka ovat vielä "
            "täysin tuoreet."
        ),
        has_lift=True,
        has_sauna=False,
        has_balcony=True,
        pets_allowed=True,
        accessible=False,
        images=_images(exterior=0, main=2, secondary=3, plan=2),
    ),
    ("Hervannan piha", "A 13"): UnitListing(
        room_layout_fi="2h + kk",
        dwelling_type="kerrostalo",
        description_fi=(
            "Kaksiossa on avokeittiö ja poikkeuksellisen iso makuuhuone, johon "
            "mahtuu helposti parisänky ja lisäksi työpiste. Taloyhtiössä on "
            "asukkaiden varattavissa oleva yhteiskäyttöauto, joka vähentää "
            "tarvetta omistaa autoa Hervannassa asuessa. Olohuone ja keittiö "
            "muodostavat yhtenäisen, valoisan kokonaisuuden. Rakennus on "
            "valmistunut 2019 ja sijaitsee lähellä kampusta ja kauppakeskusta. "
            "Sopii hyvin pariskunnalle tai kimppakämpän asukkaille."
        ),
        has_lift=True,
        has_sauna=False,
        has_balcony=False,
        pets_allowed=True,
        accessible=False,
        images=_images(exterior=0, main=3, secondary=1, plan=0),
    ),
    ("Hervannan piha", "A 26"): UnitListing(
        room_layout_fi="3h + k",
        dwelling_type="kerrostalo",
        description_fi=(
            "Kolmiossa molemmat makuuhuoneet sijaitsevat hiljaisella puolella "
            "taloa, poissa kampuksen ja kadun äänistä. Keittiöstä on käynti "
            "lasitetulle parvekkeelle, joka toimii ulko-oleskelutilana säällä "
            "kuin säällä. Olohuone on avara ja valoisa. Talo on rakennettu 2019 "
            "ja sijaitsee Hervannan keskustan tuntumassa. Ratikkayhteys "
            "keskustaan tekee kohteesta toimivan myös opiskelun jälkeiseen "
            "elämänvaiheeseen."
        ),
        has_lift=True,
        has_sauna=False,
        has_balcony=True,
        pets_allowed=True,
        accessible=False,
        images=_images(exterior=0, main=4, secondary=0, plan=1),
    ),
    ("Hervannan piha", "B 6"): UnitListing(
        room_layout_fi="2h + kk",
        dwelling_type="kerrostalo",
        description_fi=(
            "Kaksiossa on hyvä säilytystila läpi asunnon, ja kylpyhuoneesta "
            "löytyy pyykinpesukoneliitäntä, joka helpottaa arkea ilman erillistä "
            "pesutupaa. Kauppakeskus sijaitsee naapurikorttelissa, joten "
            "päivittäiset ostokset hoituvat kävellen. Avokeittiö on yhdistetty "
            "olohuoneeseen. Talo on valmistunut 2019 ja sijaitsee Hervannan "
            "ydinalueella lähellä kampusta ja palveluita. Sopii hyvin sekä "
            "opiskelijalle että työssäkäyvälle yksin asuvalle."
        ),
        has_lift=True,
        has_sauna=False,
        has_balcony=False,
        pets_allowed=True,
        accessible=False,
        images=_images(exterior=0, main=8, secondary=4, plan=2),
    ),
    ("Hervannan piha", "B 15"): UnitListing(
        room_layout_fi="4h + k + s + khh",
        dwelling_type="kerrostalo",
        description_fi=(
            "Neljän huoneen asunto perheelle tarjoaa kolme erillistä "
            "makuuhuonetta, oman saunan sekä kodinhoitohuoneen - harvinaisen "
            "kattava kokonaisuus tässä hintaluokassa. Koulu sijaitsee kadun "
            "toisella puolella, joten koulumatka on lapselle turvallinen ja "
            "lyhyt. Olohuone ja keittiö ovat avarat ja toimivat perheen "
            "yhteisenä tilana iltaisin. Rakennus on valmistunut 2019 ja "
            "sijaitsee Hervannan keskustan lähellä. Alue tarjoaa runsaasti "
            "palveluita ja hyvät ratikkayhteydet Tampereen keskustaan."
        ),
        has_lift=True,
        has_sauna=True,
        has_balcony=False,
        pets_allowed=True,
        accessible=False,
        images=_images(exterior=0, main=5, secondary=2, plan=0),
    ),
}

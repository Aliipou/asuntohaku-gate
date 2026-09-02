"""Seed properties and apartments.

All of it is invented. The addresses are real street names in the right cities
so the listings read plausibly to someone who knows the areas, but no property,
apartment, rent or price here corresponds to anything that exists.

Descriptions are written per apartment rather than generated, because a listing
page full of repeated sentences is exactly what makes a demo look like a demo.

``description_en`` is deliberately absent: SPEC section 7 makes English a
secondary locale for the search and detail pages only, and section 12 allows it
to be cut. The column stays nullable and empty until that locale is built.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class UnitSeed:
    unit_number: str
    rooms: int
    floor: int
    area_m2: Decimal
    listing_type: str
    availability: str
    description_fi: str
    rent_eur: Decimal | None = None
    price_eur: Decimal | None = None
    deposit_eur: Decimal | None = None
    available_from: dt.date | None = None


@dataclass(frozen=True, slots=True)
class PropertySeed:
    name: str
    street: str
    postal_code: str
    city: str
    housing_form: str
    built_year: int
    lat: Decimal
    lng: Decimal
    units: list[UnitSeed] = field(default_factory=list)


def _d(value: str) -> Decimal:
    return Decimal(value)


def _rent(
    unit_number: str,
    rooms: int,
    floor: int,
    area: str,
    rent: str,
    deposit: str,
    availability: str,
    description_fi: str,
    available_from: dt.date | None = None,
) -> UnitSeed:
    return UnitSeed(
        unit_number=unit_number,
        rooms=rooms,
        floor=floor,
        area_m2=_d(area),
        listing_type="vuokra",
        availability=availability,
        description_fi=description_fi,
        rent_eur=_d(rent),
        deposit_eur=_d(deposit),
        available_from=available_from,
    )


def _sale(
    unit_number: str,
    rooms: int,
    floor: int,
    area: str,
    price: str,
    availability: str,
    description_fi: str,
    available_from: dt.date | None = None,
) -> UnitSeed:
    return UnitSeed(
        unit_number=unit_number,
        rooms=rooms,
        floor=floor,
        area_m2=_d(area),
        listing_type="myynti",
        availability=availability,
        description_fi=description_fi,
        price_eur=_d(price),
        available_from=available_from,
    )


OCT = dt.date(2026, 10, 1)
NOV = dt.date(2026, 11, 1)
DEC = dt.date(2026, 12, 1)
JAN = dt.date(2027, 1, 15)

PROPERTIES: list[PropertySeed] = [
    PropertySeed(
        name="Kalliolan portti",
        street="Porthaninkatu 14",
        postal_code="00530",
        city="Helsinki",
        housing_form="vapaarahoitteinen",
        built_year=2018,
        lat=_d("60.184700"),
        lng=_d("24.951200"),
        units=[
            _rent(
                "A 12",
                1,
                3,
                "33.5",
                "895",
                "895",
                "vapaa",
                "Yksiö kolmannessa kerroksessa. Keittiö on avoin olohuoneeseen ja parveke "
                "avautuu rauhalliselle sisäpihalle. Taloyhtiössä on hissi ja asukassauna.",
            ),
            _rent(
                "A 21",
                2,
                4,
                "54.0",
                "1240",
                "1240",
                "vapautuu",
                "Kaksio, jossa makuuhuone on erotettu liukuovella. Ikkunat kahteen suuntaan, "
                "keittiössä astianpesukone. Metroasemalle kävellen kuusi minuuttia.",
                available_from=NOV,
            ),
            _rent(
                "B 4",
                2,
                1,
                "51.5",
                "1150",
                "1150",
                "vapaa",
                "Katutason kaksio omalla terassilla. Sopii hyvin koiranomistajalle: "
                "sisäänkäynti suoraan pihalta, eikä rappukäytävää tarvitse käyttää.",
            ),
            _rent(
                "B 17",
                3,
                5,
                "72.0",
                "1620",
                "1620",
                "sopimuksella",
                "Kolmio ylimmässä kerroksessa. Olohuoneesta on näkymä Kallion kirkolle. "
                "Kylpyhuone on remontoitu 2023 ja asunnossa on erillinen kodinhoitohuone.",
            ),
            _rent(
                "C 15",
                3,
                4,
                "68.5",
                "1545",
                "1545",
                "vapautuu",
                "Kolmio, jossa molemmat makuuhuoneet ovat pihan puolella. Keittiössä on "
                "tilaa ruokapöydälle kuudelle hengelle.",
                available_from=DEC,
            ),
            _sale(
                "A 30",
                2,
                6,
                "56.5",
                "329000",
                "vapaa",
                "Myytävä kaksio kuudennessa kerroksessa. Lasitettu parveke lounaaseen, "
                "keittiössä kiviset tasot. Yhtiöllä ei ole lainaa.",
            ),
            _sale(
                "B 22",
                3,
                5,
                "74.0",
                "429000",
                "sopimuksella",
                "Myytävä kolmio, jossa on läpitalon pohjaratkaisu ja kaksi parveketta. "
                "Taloyhtiö on teettänyt kuntoarvion keväällä 2026.",
            ),
            _sale(
                "C 27",
                1,
                6,
                "34.0",
                "239000",
                "vapaa",
                "Myytävä yksiö ylimmässä kerroksessa. Parveke avautuu itään ja "
                "asunnossa on tehokas pohjaratkaisu ilman hukkaneliöitä.",
            ),
            _sale(
                "B 9",
                4,
                2,
                "96.0",
                "545000",
                "vapautuu",
                "Myytävä neljän huoneen asunto, jossa on sauna ja kaksi kylpyhuonetta. "
                "Kaikki makuuhuoneet ovat sisäpihan puolella.",
                available_from=JAN,
            ),
        ],
    ),
    PropertySeed(
        name="Vallilan verstas",
        street="Sturenkatu 27",
        postal_code="00550",
        city="Helsinki",
        housing_form="tarveharkintainen",
        built_year=1974,
        lat=_d("60.194500"),
        lng=_d("24.955800"),
        units=[
            _rent(
                "A 3",
                1,
                1,
                "31.0",
                "612",
                "612",
                "vapaa",
                "Yksiö ensimmäisessä kerroksessa, ikkunat sisäpihalle. Talossa on "
                "asukastupa ja edullinen pyykkitupa.",
            ),
            _rent(
                "A 14",
                2,
                3,
                "55.5",
                "798",
                "798",
                "vapaa",
                "Kaksio, jossa on alkuperäinen mutta hyväkuntoinen parketti. Parvekkeelta "
                "näkyy Vallilan siirtolapuutarha.",
            ),
            _rent(
                "B 6",
                3,
                2,
                "77.0",
                "985",
                "985",
                "vapautuu",
                "Kolmio kahdelle lapselle: molemmat makuuhuoneet ovat omia, ja eteisessä "
                "on tilaa rattaille. Koulu ja päiväkoti ovat saman korttelin sisällä.",
                available_from=OCT,
            ),
            _rent(
                "B 19",
                4,
                4,
                "92.5",
                "1180",
                "1180",
                "sopimuksella",
                "Neljän huoneen asunto isolle ruokakunnalle. Keittiö on remontoitu 2021, "
                "ja asunnossa on kaksi erillistä wc:tä.",
            ),
            _rent(
                "C 2",
                2,
                1,
                "53.0",
                "765",
                "765",
                "vapaa",
                "Kaksio, jonka kylpyhuoneeseen mahtuu pyykinpesukone ja kuivausteline. "
                "Esteetön sisäänkäynti ja leveät oviaukot.",
            ),
            _rent(
                "C 23",
                3,
                5,
                "74.0",
                "952",
                "952",
                "vapautuu",
                "Kolmio ylimmässä kerroksessa. Olohuone on tilava ja makuuhuoneet "
                "hiljaisella puolella. Taloyhtiössä on kattosauna.",
                available_from=JAN,
            ),
        ],
    ),
    PropertySeed(
        name="Matinpuron rivi",
        street="Matinkatu 9",
        postal_code="02230",
        city="Espoo",
        housing_form="lyhyt_korkotuki",
        built_year=2021,
        lat=_d("60.160300"),
        lng=_d("24.738900"),
        units=[
            _rent(
                "1",
                2,
                1,
                "56.0",
                "1020",
                "1020",
                "vapaa",
                "Rivitalokaksio omalla pihalla. Lattialämmitys ja ilmalämpöpumppu, "
                "autokatospaikka sisältyy vuokraan.",
            ),
            _rent(
                "3",
                3,
                1,
                "78.5",
                "1290",
                "1290",
                "vapaa",
                "Kolme huonetta kahdessa kerroksessa. Yläkerrassa on kaksi makuuhuonetta "
                "ja alakerrassa avara olohuone terassiyhteydellä.",
            ),
            _rent(
                "5",
                3,
                1,
                "76.0",
                "1265",
                "1265",
                "vapautuu",
                "Päätyasunto, jossa on ikkunat kolmeen suuntaan. Pihan puolella on "
                "aidattu leikkialue.",
                available_from=NOV,
            ),
            _rent(
                "7",
                4,
                1,
                "94.0",
                "1480",
                "1480",
                "sopimuksella",
                "Perheasunto, jossa on erillinen kodinhoitohuone ja sauna. Matinkylän "
                "metroasemalle on noin kymmenen minuutin kävely.",
            ),
            _rent(
                "9",
                2,
                1,
                "54.5",
                "995",
                "995",
                "vapaa",
                "Kaksio, jonka keittiössä on astianpesukone ja induktioliesi. "
                "Asunnossa on oma varasto ja terassi etelään.",
            ),
        ],
    ),
    PropertySeed(
        name="Suvelan aukio",
        street="Kirstinkatu 12",
        postal_code="02760",
        city="Espoo",
        housing_form="asumisoikeus",
        built_year=2009,
        lat=_d("60.207400"),
        lng=_d("24.664100"),
        units=[
            _rent(
                "A 5",
                2,
                2,
                "58.0",
                "845",
                "845",
                "vapaa",
                "Asumisoikeuskaksio, jossa on lasitettu parveke ja oma sauna. "
                "Käyttövastike sisältää veden ja laajakaistan.",
            ),
            _rent(
                "A 18",
                3,
                4,
                "79.0",
                "1060",
                "1060",
                "vapautuu",
                "Kolmio, jossa keittiö ja olohuone muodostavat yhtenäisen tilan. "
                "Molemmat makuuhuoneet ovat rauhallisella puolella.",
                available_from=DEC,
            ),
            _rent(
                "B 7",
                2,
                1,
                "55.5",
                "820",
                "820",
                "vapaa",
                "Kaksio ensimmäisessä kerroksessa, terassi omalle pihalle. "
                "Sisäänkäynti on esteetön ja hissi vie kellarivarastoihin.",
            ),
            _rent(
                "B 16",
                4,
                3,
                "96.0",
                "1250",
                "1250",
                "sopimuksella",
                "Neljän huoneen asumisoikeusasunto. Kaksi kylpyhuonetta, joista "
                "toisessa on sauna. Taloyhtiön pihalla on yhteinen grillikatos.",
            ),
            _rent(
                "C 21",
                3,
                5,
                "77.5",
                "1035",
                "1035",
                "vapaa",
                "Ylimmän kerroksen kolmio, näkymä metsän suuntaan. Asunnossa on "
                "erillinen työhuoneeksi sopiva pieni makuuhuone.",
            ),
        ],
    ),
    PropertySeed(
        name="Tikkurilan asemanseutu",
        street="Kielotie 20",
        postal_code="01300",
        city="Vantaa",
        housing_form="tarveharkintainen",
        built_year=1988,
        lat=_d("60.292300"),
        lng=_d("25.043700"),
        units=[
            _rent(
                "A 7",
                1,
                2,
                "32.0",
                "545",
                "545",
                "vapaa",
                "Yksiö juna-aseman vieressä. Lentokentälle pääsee kehäradalla "
                "vaihtamatta. Talossa on hissi ja valvottu pyöräkellari.",
            ),
            _rent(
                "A 22",
                2,
                5,
                "57.0",
                "735",
                "735",
                "vapaa",
                "Kaksio viidennessä kerroksessa, parveke länteen. Keittiössä on "
                "tilaa ruokapöydälle ja asunnossa iso vaatehuone.",
            ),
            _rent(
                "B 3",
                3,
                1,
                "75.5",
                "915",
                "915",
                "vapautuu",
                "Kolmio, jonka pohjaratkaisu on toimiva pienelle perheelle. "
                "Päiväkoti, kirjasto ja uimahalli ovat kävelymatkan päässä.",
                available_from=OCT,
            ),
            _rent(
                "B 14",
                4,
                3,
                "89.0",
                "1095",
                "1095",
                "sopimuksella",
                "Neljän huoneen asunto, jossa on kolme makuuhuonetta ja erillinen "
                "keittiö. Sopii ruokakunnalle, jossa on useampi lapsi.",
            ),
            _rent(
                "C 6",
                2,
                2,
                "54.0",
                "705",
                "705",
                "vapaa",
                "Kaksio sisäpihan puolella, hyvin hiljainen. Kylpyhuone on uusittu "
                "2020 ja putkiremontti on tehty koko taloon.",
            ),
            _rent(
                "C 27",
                3,
                6,
                "72.0",
                "885",
                "885",
                "vapautuu",
                "Kolmio ylimmässä kerroksessa. Olohuoneesta näkee radan yli "
                "Tikkurilanjoelle. Taloyhtiössä on kattoterassi.",
                available_from=JAN,
            ),
        ],
    ),
    PropertySeed(
        name="Myyrmäen tori",
        street="Liesitori 3",
        postal_code="01600",
        city="Vantaa",
        housing_form="vapaarahoitteinen",
        built_year=2015,
        lat=_d("60.261500"),
        lng=_d("24.855400"),
        units=[
            _rent(
                "A 9",
                2,
                3,
                "55.0",
                "1010",
                "1010",
                "vapaa",
                "Kaksio torin laidalla. Kauppa, apteekki ja juna-asema ovat saman "
                "aukion ympärillä. Parveke on lasitettu.",
            ),
            _rent(
                "A 24",
                3,
                6,
                "71.5",
                "1310",
                "1310",
                "vapautuu",
                "Kolmio kuudennessa kerroksessa, näkymä Vantaanjoelle. Asunnossa on "
                "oma sauna ja lasitettu parveke.",
                available_from=NOV,
            ),
            _rent(
                "B 2",
                1,
                1,
                "34.0",
                "790",
                "790",
                "vapaa",
                "Yksiö, jossa on iso ikkuna ja tehokas keittiönurkkaus. "
                "Sisäänkäynnin vieressä on oma varasto.",
            ),
            _rent(
                "B 12",
                2,
                4,
                "52.5",
                "985",
                "985",
                "sopimuksella",
                "Kaksio, jonka makuuhuoneeseen mahtuu parisänky ja työpöytä. "
                "Taloyhtiössä on kuntosali ja kaksi saunaosastoa.",
            ),
            _sale(
                "A 31",
                2,
                7,
                "58.0",
                "268000",
                "vapaa",
                "Myytävä kaksio ylimmässä kerroksessa. Lasitettu parveke lounaaseen "
                "ja avara olohuone. Hissi tuo asunnon ovelle asti.",
            ),
            _sale(
                "B 20",
                3,
                5,
                "73.5",
                "339000",
                "vapautuu",
                "Myytävä kolmio, jossa on sauna ja kaksi parveketta. Taloyhtiön "
                "lainaosuus on maksettavissa pois kerralla.",
                available_from=DEC,
            ),
            _sale(
                "C 5",
                1,
                2,
                "36.5",
                "189000",
                "vapaa",
                "Myytävä yksiö ensiasunnon ostajalle tai sijoittajaksi. Alue on "
                "vuokrattavaa asuntokantaa kysyttyä opiskelijoiden keskuudessa.",
            ),
            _sale(
                "A 14",
                4,
                4,
                "92.0",
                "398000",
                "sopimuksella",
                "Myytävä neljän huoneen asunto, jossa on sauna ja lasitettu parveke. "
                "Taloyhtiöön on tehty julkisivuremontti vuonna 2024.",
            ),
        ],
    ),
    PropertySeed(
        name="Kalevan kaari",
        street="Sammonkatu 44",
        postal_code="33540",
        city="Tampere",
        housing_form="asumisoikeus",
        built_year=2012,
        lat=_d("61.494700"),
        lng=_d("23.812400"),
        units=[
            _rent(
                "A 4",
                2,
                1,
                "56.5",
                "715",
                "715",
                "vapaa",
                "Asumisoikeuskaksio, jossa on oma piha-alue ja varasto. "
                "Kalevan kirkolle ja uimahallille on lyhyt kävelymatka.",
            ),
            _rent(
                "A 17",
                3,
                3,
                "78.0",
                "925",
                "925",
                "vapautuu",
                "Kolmio, jossa on sauna ja lasitettu parveke. Keittiössä on "
                "astianpesukone ja erillinen ruokailutila.",
                available_from=OCT,
            ),
            _rent(
                "B 8",
                1,
                2,
                "37.0",
                "585",
                "585",
                "vapaa",
                "Yksiö, jonka ikkunat avautuvat puistoon. Käyttövastike sisältää "
                "veden ja taloyhtiön laajakaistan.",
            ),
            _rent(
                "B 19",
                4,
                4,
                "97.5",
                "1120",
                "1120",
                "sopimuksella",
                "Neljän huoneen asunto, kaksi kylpyhuonetta ja iso eteinen. "
                "Ratikkapysäkki on talon edessä.",
            ),
        ],
    ),
    PropertySeed(
        name="Hervannan piha",
        street="Insinöörinkatu 60",
        postal_code="33720",
        city="Tampere",
        housing_form="lyhyt_korkotuki",
        built_year=2019,
        lat=_d("61.448600"),
        lng=_d("23.855300"),
        units=[
            _rent(
                "A 2",
                1,
                1,
                "31.5",
                "560",
                "560",
                "vapaa",
                "Yksiö yliopiston kampuksen läheisyydessä. Kalustettu keittiö ja "
                "oma parveke. Ratikalla keskustaan noin 20 minuuttia.",
            ),
            _rent(
                "A 13",
                2,
                3,
                "53.5",
                "760",
                "760",
                "vapaa",
                "Kaksio, jossa on avokeittiö ja iso makuuhuone. Taloyhtiössä on "
                "yhteiskäyttöauto asukkaiden varattavissa.",
            ),
            _rent(
                "A 26",
                3,
                5,
                "73.0",
                "965",
                "965",
                "vapautuu",
                "Kolmio, jonka molemmat makuuhuoneet ovat hiljaisella puolella. "
                "Keittiöstä on käynti lasitetulle parvekkeelle.",
                available_from=NOV,
            ),
            _rent(
                "B 6",
                2,
                2,
                "51.0",
                "735",
                "735",
                "vapaa",
                "Kaksio, jossa on hyvä säilytystila ja kylpyhuoneessa "
                "pyykinpesukoneliitäntä. Kauppakeskus on naapurikorttelissa.",
            ),
            _rent(
                "B 15",
                4,
                4,
                "88.5",
                "1090",
                "1090",
                "sopimuksella",
                "Neljän huoneen asunto perheelle. Kolme makuuhuonetta, sauna ja "
                "kodinhoitohuone. Koulu on kadun toisella puolella.",
            ),
        ],
    ),
]

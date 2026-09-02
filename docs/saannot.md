# Sääntöluettelo

<!-- Tämä tiedosto on generoitu. Älä muokkaa käsin. -->
<!-- Generated file. Do not edit by hand; run `python -m api.catalogue --write`. -->

Jokainen asunnon kelpoisuuspäätös syntyy jostakin alla olevasta säännöstä ja kertoo hakijalle sekä säännön tunnuksen että sen arvon, joka päätökseen johti.

Lopputuloksia on kolme: **kelpoinen**, **puuttuvat tiedot** ja **ei kelpoinen**. Puuttuva tieto ei ole hylkäys vaan pyyntö täydentää hakemusta.

Sarake *Tarvitsee hakemukselta* kertoo, mitä hakulomake kysyy, kun hakemuksella on kyseisen asumismuodon asunto. Lomake kootaan näistä tiedoista, joten uusi sääntö muuttaa lomaketta ilman erillistä muutosta käyttöliittymään.

## Kaikki säännöt

| Tunnus | Sääntö | Laji | Tarvitsee hakemukselta |
| --- | --- | --- | --- |
| `ASO-JARJ-01` | Asumisoikeusnumero on annettu ja oikean muotoinen | kelpoisuussääntö | asumisoikeusnumero |
| `ASO-JARJ-02` | Hakijoiden järjestys asumisoikeusnumeron mukaan | järjestyssääntö | asumisoikeusnumero |
| `ASO-VARALLISUUS-01` | Varallisuusraja, josta yli 55-vuotiaat on vapautettu | kelpoisuussääntö | ruokakunnan varallisuus, ruokakunnan koko |
| `LYHYT-EI-VARALLISUUS-01` | Varallisuutta ja asunnontarvetta ei kysytä | valvontasääntö | – |
| `LYHYT-TULO-01` | Ruokakunnan tulot enintään tulorajan suuruiset | kelpoisuussääntö | ruokakunnan tulot, ruokakunnan koko |
| `TARVE-SIJOITUS-01` | Hakijoiden järjestys tarveharkinnassa | järjestyssääntö | asunnontarve, ruokakunnan varallisuus, ruokakunnan tulot |
| `TARVE-TARVE-01` | Asunnontarve on ilmoitettu | kelpoisuussääntö | asunnontarve |
| `TARVE-TULO-01` | Ruokakunnan tulot enintään tulorajan suuruiset | kelpoisuussääntö | ruokakunnan tulot, ruokakunnan koko |
| `TARVE-VARALLISUUS-01` | Ruokakunnan varallisuus enintään varallisuusrajan suuruinen | kelpoisuussääntö | ruokakunnan varallisuus |
| `VAPAA-LUOTTO-01` | Luottotiedot on selvitetty | kelpoisuussääntö | luottotiedot |
| `VAPAA-MAKSU-01` | Tulot riittävät vuokraan | kelpoisuussääntö | ruokakunnan tulot |
| `VAPAA-VAKUUS-01` | Vakuus on hyväksytty | kelpoisuussääntö | vakuuden hyväksyminen |
| `YLEIS-KOKO-01` | Ruokakunnan koko suhteessa asunnon kokoon | kelpoisuussääntö | ruokakunnan koko |
| `YLEIS-VANHENTUNUT-01` | Hakemuksen voimassaolo | kelpoisuussääntö | – |

## Säännöt asumismuodoittain

### Vapaarahoitteinen vuokra-asunto

Avoin haku. Tuloja verrataan vain vuokranmaksukykyyn, eikä varallisuutta tai asunnontarvetta kysytä.

#### VAPAA-LUOTTO-01 — Luottotiedot on selvitetty

Maksuhäiriömerkintä ei yksin johda hylkäämiseen. Merkinnän kohdalla hakijalta pyydetään selvitys, jolloin päätös on puuttuvat tiedot eikä ei kelpoinen.

- **Laji:** kelpoisuussääntö
- **Tarvitsee hakemukselta:** luottotiedot
- **Mahdolliset lopputulokset:** kelpoinen, puuttuvat tiedot

#### VAPAA-MAKSU-01 — Tulot riittävät vuokraan

Vuokra saa olla enintään määritellyn osuuden ruokakunnan bruttotuloista. Tulon lähdettä ei eroteta: etuudet lasketaan samalla tavalla kuin palkka.

- **Laji:** kelpoisuussääntö
- **Tarvitsee hakemukselta:** ruokakunnan tulot
- **Mahdolliset lopputulokset:** kelpoinen, puuttuvat tiedot, ei kelpoinen

#### VAPAA-VAKUUS-01 — Vakuus on hyväksytty

Hakija on vahvistanut, että voi maksaa asunnon vakuuden.

- **Laji:** kelpoisuussääntö
- **Tarvitsee hakemukselta:** vakuuden hyväksyminen
- **Mahdolliset lopputulokset:** kelpoinen, puuttuvat tiedot, ei kelpoinen

### Lyhyen korkotuen vuokra-asunto

Ruokakunnan tulot tarkistetaan. Varallisuutta ja asunnontarvetta ei kysytä, ja sääntö LYHYT-EI-VARALLISUUS-01 valvoo sitä.

#### LYHYT-EI-VARALLISUUS-01 — Varallisuutta ja asunnontarvetta ei kysytä

Tarkistaa, ettei päätöstä tehtäessä luettu varallisuus- tai asunnontarvetietoja. Sääntö on olemassa, jotta regressio, joka alkaa kysyä pienituloisilta hakijoilta varallisuustietoja, kaatuu testissä.

- **Laji:** valvontasääntö
- **Tarvitsee hakemukselta:** –
- **Mahdolliset lopputulokset:** kelpoinen, ei kelpoinen

#### LYHYT-TULO-01 — Ruokakunnan tulot enintään tulorajan suuruiset

Ruokakunnan bruttotulot verrataan tulorajaan, joka määräytyy ruokakunnan koon ja kohteen sijaintikunnan mukaan.

- **Laji:** kelpoisuussääntö
- **Tarvitsee hakemukselta:** ruokakunnan tulot, ruokakunnan koko
- **Mahdolliset lopputulokset:** kelpoinen, puuttuvat tiedot, ei kelpoinen

### Tarveharkintainen vuokra-asunto

Tulot, varallisuus ja asunnontarve arvioidaan, ja hakijat asetetaan keskenään järjestykseen.

#### TARVE-SIJOITUS-01 — Hakijoiden järjestys tarveharkinnassa

Järjestys: kiireellisin asunnontarve ensin, sitten pienin varallisuus, sitten pienimmät tulot. Yhtä kiireelliset hakemukset järjestetään jättöpäivän mukaan, ei koskaan satunnaisesti.

- **Laji:** järjestyssääntö
- **Tarvitsee hakemukselta:** asunnontarve, ruokakunnan varallisuus, ruokakunnan tulot
- **Mahdolliset lopputulokset:** järjestysnumero

#### TARVE-TARVE-01 — Asunnontarve on ilmoitettu

Hakijan on kerrottava asuntotilanteensa. Vastaus 'ei erityistä asunnontarvetta' on kelvollinen vastaus eikä estä hakemista; se vaikuttaa hakijoiden järjestykseen säännössä TARVE-SIJOITUS-01.

- **Laji:** kelpoisuussääntö
- **Tarvitsee hakemukselta:** asunnontarve
- **Mahdolliset lopputulokset:** kelpoinen, puuttuvat tiedot

#### TARVE-TULO-01 — Ruokakunnan tulot enintään tulorajan suuruiset

Ruokakunnan bruttotulot verrataan tulorajaan, joka määräytyy ruokakunnan koon ja kohteen sijaintikunnan mukaan.

- **Laji:** kelpoisuussääntö
- **Tarvitsee hakemukselta:** ruokakunnan tulot, ruokakunnan koko
- **Mahdolliset lopputulokset:** kelpoinen, puuttuvat tiedot, ei kelpoinen

#### TARVE-VARALLISUUS-01 — Ruokakunnan varallisuus enintään varallisuusrajan suuruinen

Ruokakunnan yhteenlaskettu varallisuus verrataan varallisuusrajaan.

- **Laji:** kelpoisuussääntö
- **Tarvitsee hakemukselta:** ruokakunnan varallisuus
- **Mahdolliset lopputulokset:** kelpoinen, puuttuvat tiedot, ei kelpoinen

### Asumisoikeusasunto

Tulorajaa ei ole. Hakemiseen tarvitaan järjestysnumero, ja asunto tarjotaan pienimmän numeron mukaan.

#### ASO-JARJ-01 — Asumisoikeusnumero on annettu ja oikean muotoinen

Asumisoikeusasuntoon tarvitaan järjestysnumero. Puuttuva numero on puuttuva tieto, ei hylkäys; väärän muotoinen numero hylätään.

- **Laji:** kelpoisuussääntö
- **Tarvitsee hakemukselta:** asumisoikeusnumero
- **Mahdolliset lopputulokset:** kelpoinen, puuttuvat tiedot, ei kelpoinen

#### ASO-JARJ-02 — Hakijoiden järjestys asumisoikeusnumeron mukaan

Asunto tarjotaan pienimmän järjestysnumeron mukaan. Hakijat, joilta numero puuttuu tai on väärän muotoinen, eivät ole jonossa: heidät pysäyttää sääntö ASO-JARJ-01.

- **Laji:** järjestyssääntö
- **Tarvitsee hakemukselta:** asumisoikeusnumero
- **Mahdolliset lopputulokset:** järjestysnumero

#### ASO-VARALLISUUS-01 — Varallisuusraja, josta yli 55-vuotiaat on vapautettu

Ruokakunnan varallisuus verrataan varallisuusrajaan. Jos ruokakunnan kaikki aikuiset hakijat ovat täyttäneet vapautusiän, raja ei koske hakemusta ja päätös on kelpoinen riippumatta varallisuudesta.

- **Laji:** kelpoisuussääntö
- **Tarvitsee hakemukselta:** ruokakunnan varallisuus, ruokakunnan koko
- **Mahdolliset lopputulokset:** kelpoinen, puuttuvat tiedot, ei kelpoinen

### Kaikkia asumismuotoja koskevat säännöt

#### YLEIS-KOKO-01 — Ruokakunnan koko suhteessa asunnon kokoon

Liian suuri ruokakunta asuntoon on hylkäys. Ruokakuntaan nähden suuri asunto ei ole este: päätös on kelpoinen ja hakijalle kerrotaan, että suurempi ruokakunta voi saada etusijan.

- **Laji:** kelpoisuussääntö
- **Tarvitsee hakemukselta:** ruokakunnan koko
- **Mahdolliset lopputulokset:** kelpoinen, puuttuvat tiedot, ei kelpoinen

#### YLEIS-VANHENTUNUT-01 — Hakemuksen voimassaolo

Hakemus on voimassa määrätyn ajan jättöpäivästä. Vanhentunut hakemus ei ole hylätty: kaikkien asuntojen päätökseksi tulee puuttuvat tiedot ja hakijaa pyydetään vahvistamaan tiedot muokkauslinkistä.

- **Laji:** kelpoisuussääntö
- **Tarvitsee hakemukselta:** –
- **Mahdolliset lopputulokset:** kelpoinen, puuttuvat tiedot

## Käytetyt rajat

**Kaikki alla olevat luvut on keksitty tätä demoa varten.** Ne eivät ole voimassa olevia lakisääteisiä rajoja eivätkä peräisin mistään asuntotoimijalta. Luvut ovat tiedostossa `seeds/limits.py`, joka on ainoa paikka koko projektissa, jossa niitä säilytetään.

### Tulorajat, bruttotulot euroa kuukaudessa

**vapaarahoitteinen vuokra-asunto:** ei tulorajaa.

**lyhyen korkotuen vuokra-asunto**

| Ruokakunnan koko | Pääkaupunkiseutu | Muu Suomi |
| --- | --- | --- |
| 1 henki | 3 800 € | 3 400 € |
| 2 henkeä | 5 600 € | 5 000 € |
| 3 henkeä | 7 100 € | 6 400 € |
| 4 henkeä | 8 400 € | 7 600 € |
| jokainen seuraava henkilö | 1 100 € | 1 100 € |

**tarveharkintainen vuokra-asunto**

| Ruokakunnan koko | Pääkaupunkiseutu | Muu Suomi |
| --- | --- | --- |
| 1 henki | 3 100 € | 2 800 € |
| 2 henkeä | 4 600 € | 4 200 € |
| 3 henkeä | 5 900 € | 5 300 € |
| 4 henkeä | 7 000 € | 6 300 € |
| jokainen seuraava henkilö | 900 € | 900 € |

**asumisoikeusasunto:** ei tulorajaa.

### Varallisuusrajat

| Asumismuoto | Ruokakunnan varallisuus enintään |
| --- | --- |
| vapaarahoitteinen vuokra-asunto | ei varallisuusrajaa |
| lyhyen korkotuen vuokra-asunto | ei varallisuusrajaa |
| tarveharkintainen vuokra-asunto | 42 000 € |
| asumisoikeusasunto | 95 000 € |

### Muut rajat

| Raja | Arvo |
| --- | --- |
| Vuokran enimmäisosuus bruttotuloista | 35 % |
| Ikä, josta alkaen varallisuusraja ei koske asumisoikeushakijaa | 55 vuotta |
| Täysi-ikäisyys | 18 vuotta |
| Asukkaita enintään huonetta kohden | 2 |
| Huoneiden ero, josta asunnosta huomautetaan suureksi | 2 |
| Hakemuksen voimassaolo | 3 kuukautta |
| Asumisoikeusnumeron muoto | `^\d{6}$` |

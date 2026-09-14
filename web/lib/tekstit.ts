/**
 * All Finnish UI chrome strings for the frontend, in one module, per
 * asuntohaku-gate-SPEC.md section 7 ("Finnish first").
 *
 * What does NOT belong here: decision messages, rule titles and outcome
 * labels. Those come from the API already in Finnish (message_fi,
 * rule_title_fi, outcome_label_fi, housing_form_label_fi, ...) so that a
 * decision can never be rendered without the exact reason that produced it —
 * duplicating that text here would risk it drifting out of sync with the
 * rule engine.
 */

import type { Availability, HousingForm, ListingType } from "./api";

export const tekstit = {
  // Page
  sivunOtsikko: "Asuntohaku",

  // Segmented control (listing type)
  vuokrattavat: "Vuokrattavat",
  myytavat: "Myytävät",
  valitseVuokraTaiMyynti: "Vuokrattavat vai myytävät",

  // Search bar / filter chips
  kaupunki: "Kaupunki",
  kaupunkiPlaceholder: "Esim. Helsinki",
  huoneet: "Huoneita",
  huoneitaVahintaan: "Vähintään",
  huoneitaEnintaan: "Enintään",
  hintahaarukka: "Hinta",
  hintaVuokraLabel: "Vuokra (€/kk)",
  hintaMyyntiLabel: "Hinta (€)",
  hintaAlkaen: "Alkaen",
  hintaEnintaan: "Enintään",
  asumismuoto: "Asumismuoto",
  vapautuminen: "Vapautuminen",
  lisaaHakuehtoja: "Lisää hakuehtoja",
  kaikki: "Kaikki",
  hae: "Hae",
  nollaaHakuehdot: "Nollaa hakuehdot",

  // Results header / sort
  jarjestys: "Järjestys",
  uusimmat: "Uusimmat",
  halvinEnsin: "Halvin ensin",
  kalleinEnsin: "Kallein ensin",
  suurinPintaAla: "Suurin pinta-ala",
  tallennaHaku: "Tallenna haku",
  hakuTallennettu: "Haku tallennettu",

  // Result count (Finnish partitive plural: "1 asunto" but "2 asuntoa")
  tulosMaara(n: number): string {
    return n === 1 ? "1 asunto" : `${n} asuntoa`;
  },

  // Errors / empty states
  hakuEpaonnistui: "Hakua ei voitu ladata juuri nyt. Yritä hetken kuluttua uudelleen.",
  eiTuloksia: "Hakuehdoilla ei löytynyt yhtään asuntoa. Kokeile väljempiä hakuehtoja.",

  // Result card
  kuvaPuuttuu: "Ei kuvaa",
  lisaaSuosikkeihin: "Lisää suosikkeihin",
  poistaSuosikeista: "Poista suosikeista",
  vuokra: "Vuokra",
  vakuus: "Vakuus",
  velatonHinta: "Velaton hinta",
  hoitovastike: "Hoitovastike",
  eiTiedossa: "Ei tiedossa",
  kuukausi: "kk",

  // Map
  kartta: "Kartta",

  // Listing page (asunnot/[id]) — gallery
  pohjapiirros: "Pohjapiirros",
  edellinenKuva: "Edellinen kuva",
  seuraavaKuva: "Seuraava kuva",
  kuvaNumero(n: number, total: number): string {
    return `Kuva ${n}/${total}`;
  },

  // Listing page — dense key-facts table (spec section 7's exact labels)
  sijainti: "Sijainti",
  huoneistoselitelma: "Huoneistoselitelmä",
  pintaAla: "Pinta-ala",
  kerrosFakta: "Kerros",
  vapautuuFakta: "Vapautuu",
  rakennusvuosi: "Rakennusvuosi",
  hissi: "Hissi",
  saunaFakta: "Sauna",
  parveke: "Parveke",
  lemmikit: "Lemmikit",
  esteeton: "Esteetön",
  kylla: "Kyllä",
  ei: "Ei",

  // Listing page — one sentence on what the housing form asks, linking onward
  lueHakemuksesta: "Lue hakemuksesta",

  // Listing page — action panel
  yhteyshenkilo: "Yhteyshenkilö",
  soita: "Soita",
  lahetaSahkopostia: "Lähetä sähköpostia",
  lisaaHakemukseen: "Lisää hakemukseen",
  lisattyHakemukseen: "Lisätty hakemukseen",
  aloitaHakemus: "Aloita hakemus lisäämällä tämä asunto",
  avaaHakemus: "Avaa hakemus",
  varaaNayttoaika: "Varaa näyttöaika",
  jataTarjous: "Jätä tarjous",
  eiNaytettavissa: "Ei tulevia näyttöaikoja tällä hetkellä.",
  paikkojaJaljella(n: number): string {
    return n === 1 ? "1 paikka jäljellä" : `${n} paikkaa jäljellä`;
  },
  taynna: "Täynnä",
  varaaValittuAika: "Varaa valittu aika",
  naytonVarausOnnistui: "Näyttöaika varattu. Vahvistus lähetetään hakemuksen yhteystietoihin.",
  naytonVarausEpaonnistui: "Näyttöaikaa ei voitu varata. Se saattoi juuri täyttyä — kokeile toista aikaa.",
  tarvitaanHakemusEnsin: "Näyttöajan varaaminen vaatii hakemuksen. Aloita hakemus ensin.",

  // Listing page — offer form (sale units)
  tarjoajanNimi: "Nimi",
  sahkoposti: "Sähköposti",
  tarjousSumma: "Tarjoussumma (€)",
  viestiValinnainen: "Viesti (valinnainen)",
  lahetaTarjousPainike: "Lähetä tarjous",
  tarjousLahetetty: "Tarjous lähetetty. Yhteyshenkilö on sinuun yhteydessä.",
  tarjousEpaonnistui: "Tarjousta ei voitu lähettää. Tarkista tiedot ja yritä uudelleen.",

  // Listing page — similar units, errors, locale toggle
  vastaaviaAsuntoja: "Vastaavia asuntoja",
  asuntoaEiLoytynyt: "Asuntoa ei löytynyt.",
  asunnonLataaminenEpaonnistui: "Asunnon tietoja ei voitu ladata juuri nyt.",
  takaisinHakuun: "Takaisin hakuun",
  inEnglish: "In English",
  suomeksi: "Suomeksi",
};

/**
 * Static Finnish labels for the housing-form filter control. Distinct from
 * `housing_form_label_fi` on a UnitOut — that is the label for one already-
 * fetched unit; this is what the filter <select> needs before any unit has
 * been fetched.
 */
export const ASUMISMUOTO_LABELS: Record<HousingForm, string> = {
  vapaarahoitteinen: "Vapaarahoitteinen",
  lyhyt_korkotuki: "Lyhyen korkotuen",
  tarveharkintainen: "Tarveharkintainen",
  asumisoikeus: "Asumisoikeus",
};

export const AVAILABILITY_LABELS: Record<Availability, string> = {
  vapaa: "Vapaa",
  vapautuu: "Vapautuu",
  sopimuksella: "Sopimuksella",
};

export const LISTING_TYPE_LABELS: Record<ListingType, string> = {
  vuokra: tekstit.vuokrattavat,
  myynti: tekstit.myytavat,
};

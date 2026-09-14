/**
 * Finnish-only UI chrome for the application, decisions and admin screens
 * (Hakemus, Päätökset, Asukasvalinta). Deliberately separate from
 * lib/tekstit.ts: that module is typed against an English mirror
 * (lib/tekstit.en.ts) because the search and detail pages have a secondary
 * locale, and these three screens must not — SPEC section 7 says so
 * explicitly ("do not half-translate the application flow"). Keeping them in
 * a different file makes that a structural fact, not a habit to remember.
 *
 * What does NOT belong here: decision messages, rule titles, outcome labels
 * and evidence text. Those come from the API already in Finnish
 * (message_fi, rule_title_fi, outcome_label_fi, ranking_basis_fi, ...).
 */

import type { MemberRole, NeedSituation, OutcomeValue } from "./api";

export const sovellusTekstit = {
  // Hakemus — basket
  hakemuksenOtsikko: "Hakemus",
  ostoskori: "Valitut asunnot",
  poistaKorista: "Poista hakemuksesta",
  koriOnTyhja: "Et ole vielä lisännyt yhtään asuntoa hakemukseen.",
  etsiAsuntoja: "Etsi asuntoja",
  katsoPaatokset: "Katso päätökset",

  // Hakemus — contact section
  yhteystiedot: "Yhteystiedot",
  nimi: "Nimi",
  sahkopostiosoite: "Sähköposti",
  puhelin: "Puhelin",

  // Hakemus — progress, expressed as what's missing (never a percentage)
  puuttuuViela: "Vielä puuttuu:",
  eiPuuttuviaTietoja: "Kaikki tarvittavat tiedot on annettu.",
  vaatiiAsunnon(unitLabel: string, ruleTitle: string): string {
    return `${unitLabel} vaatii tämän (${ruleTitle})`;
  },

  // Hakemus — household section (household_income / assets / household_size)
  ruokakuntaOtsikko: "Ruokakunta",
  lisaaHenkilo: "Lisää henkilö",
  poistaHenkilo: "Poista",
  rooli: "Rooli",
  syntymavuosi: "Syntymävuosi",
  bruttotulot: "Bruttotulot (€/kk)",
  varallisuus: "Varallisuus (€)",

  // Hakemus — housing need section
  asunnontarveOtsikko: "Asunnon tarve",
  tilanne: "Tilanne",
  kiireellisyysValinnainen: "Lisätietoa tilanteesta (valinnainen)",

  // Hakemus — order number section
  asumisoikeusnumeroOtsikko: "Asumisoikeusnumero",
  asumisoikeusnumero: "Numero",

  // Hakemus — deposit section
  vakuusOtsikko: "Vakuus",
  hyvaksynVakuuden: "Hyväksyn vakuuden ehdot",

  // Hakemus — credit record section
  luottotiedotOtsikko: "Luottotiedot",
  onkoMaksuhairioita: "Onko sinulla maksuhäiriömerkintöjä?",
  kylla: "Kyllä",
  ei: "Ei",

  // Hakemus — save
  tallenna: "Tallenna tiedot",
  tallennettu: "Tiedot tallennettu.",
  tallennusEpaonnistui: "Tietoja ei voitu tallentaa. Tarkista tiedot ja yritä uudelleen.",

  // Hakemus — errors
  hakemustaEiLoytynyt: "Hakemusta ei löytynyt. Tarkista muokkauslinkki.",
  hakemuksenLataaminenEpaonnistui: "Hakemuksen tietoja ei voitu ladata juuri nyt.",

  // Päätökset
  paatoksetOtsikko: "Päätökset",
  peruste: "Peruste",
  ratkaisevatTiedot: "Ratkaisevat tiedot",
  taydennaHakemuksessa: "Täydennä hakemuksessa",
  eiPaatoksia: "Hakemuksessa ei ole vielä yhtään asuntoa.",
  takaisinHakemukseen: "Takaisin hakemukseen",

  // Asukasvalinta (admin)
  asukasvalintaOtsikko: "Asukasvalinta",
  sija: "Sija",
  hakija: "Hakija",
  hakijaNimeton: "Nimetön hakija",
  kelpoisuus: "Kelpoisuus",
  jarjestysperuste: "Järjestysperuste",
  eiJarjestyssaantoa: "Tälle asumismuodolle ei ole järjestyssääntöä; hakijat eivät ole keskenään ranking-järjestyksessä.",
  eiHakijoita: "Tälle asunnolle ei ole vielä hakijoita.",
} as const;

export const MEMBER_ROLE_LABELS: Record<MemberRole, string> = {
  paahakija: "Pääasiallinen hakija",
  toinen: "Toinen hakija",
  muu: "Muu ruokakunnan jäsen",
};

export const NEED_SITUATION_LABELS: Record<NeedSituation, string> = {
  asunnoton: "Asunnoton",
  irtisanottu: "Irtisanottu nykyisestä asunnosta",
  ahtaasti: "Asuu ahtaasti",
  ei_tarvetta: "Ei erityistä asunnontarvetta",
};

/** Outcome names, not decision text — the wording itself always comes from the API. */
export const OUTCOME_LABELS_FI: Record<OutcomeValue, string> = {
  kelpoinen: "Kelpoinen",
  puuttuvat_tiedot: "Puuttuvat tiedot",
  ei_kelpoinen: "Ei kelpoinen",
};

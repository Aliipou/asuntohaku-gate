/**
 * English mirror of lib/tekstit.ts, for the search and detail pages only
 * (asuntohaku-gate-SPEC.md section 7: "English is a secondary locale for the
 * search and detail pages only — do not half-translate the application
 * flow"). Nothing here is imported by the application, decisions or admin
 * screens; those stay Finnish-only, always.
 *
 * Typed as `typeof tekstit` so adding a key to tekstit.ts without adding it
 * here is a type error instead of a silently half-translated page.
 */

import type { Availability, HousingForm, ListingType } from "./api";
import { tekstit } from "./tekstit";

export const tekstitEn: typeof tekstit = {
  // Page
  sivunOtsikko: "Home search",

  // Segmented control (listing type)
  vuokrattavat: "For rent",
  myytavat: "For sale",
  valitseVuokraTaiMyynti: "For rent or for sale",

  // Search bar / filter chips
  kaupunki: "City",
  kaupunkiPlaceholder: "e.g. Helsinki",
  huoneet: "Rooms",
  huoneitaVahintaan: "At least",
  huoneitaEnintaan: "At most",
  hintahaarukka: "Price",
  hintaVuokraLabel: "Rent (€/month)",
  hintaMyyntiLabel: "Price (€)",
  hintaAlkaen: "From",
  hintaEnintaan: "Up to",
  asumismuoto: "Housing form",
  vapautuminen: "Availability",
  lisaaHakuehtoja: "More filters",
  kaikki: "All",
  hae: "Search",
  nollaaHakuehdot: "Clear filters",

  // Results header / sort
  jarjestys: "Sort",
  uusimmat: "Newest",
  halvinEnsin: "Cheapest first",
  kalleinEnsin: "Most expensive first",
  suurinPintaAla: "Largest floor area",
  tallennaHaku: "Save search",
  hakuTallennettu: "Search saved",

  tulosMaara(n: number): string {
    return n === 1 ? "1 home" : `${n} homes`;
  },

  // Errors / empty states
  hakuEpaonnistui: "The search couldn't be loaded right now. Try again shortly.",
  eiTuloksia: "No homes matched these filters. Try widening your search.",

  // Result card
  kuvaPuuttuu: "No photo",
  lisaaSuosikkeihin: "Add to favourites",
  poistaSuosikeista: "Remove from favourites",
  vuokra: "Rent",
  vakuus: "Deposit",
  velatonHinta: "Sale price",
  hoitovastike: "Maintenance fee",
  eiTiedossa: "Not available",
  kuukausi: "mo",

  // Map
  kartta: "Map",

  // Listing page — gallery
  pohjapiirros: "Floor plan",
  edellinenKuva: "Previous photo",
  seuraavaKuva: "Next photo",
  kuvaNumero(n: number, total: number): string {
    return `Photo ${n}/${total}`;
  },

  // Listing page — dense key-facts table
  sijainti: "Location",
  huoneistoselitelma: "Room layout",
  pintaAla: "Floor area",
  kerrosFakta: "Floor",
  vapautuuFakta: "Available",
  rakennusvuosi: "Built",
  hissi: "Lift",
  saunaFakta: "Sauna",
  parveke: "Balcony",
  lemmikit: "Pets",
  esteeton: "Accessible",
  kylla: "Yes",
  ei: "No",

  // Listing page — housing-form explanation link
  lueHakemuksesta: "Read about the application",

  // Listing page — action panel
  yhteyshenkilo: "Contact",
  soita: "Call",
  lahetaSahkopostia: "Send an email",
  lisaaHakemukseen: "Add to application",
  lisattyHakemukseen: "Added to application",
  aloitaHakemus: "Start an application by adding this home",
  avaaHakemus: "Open application",
  varaaNayttoaika: "Book a viewing",
  jataTarjous: "Make an offer",
  eiNaytettavissa: "No upcoming viewings right now.",
  paikkojaJaljella(n: number): string {
    return n === 1 ? "1 spot left" : `${n} spots left`;
  },
  taynna: "Full",
  varaaValittuAika: "Book the selected time",
  naytonVarausOnnistui: "Viewing booked. A confirmation will go to the application's contact details.",
  naytonVarausEpaonnistui: "Couldn't book that viewing — it may have just filled up. Try another time.",
  tarvitaanHakemusEnsin: "Booking a viewing needs an application. Start one first.",

  // Listing page — offer form
  tarjoajanNimi: "Name",
  sahkoposti: "Email",
  tarjousSumma: "Offer amount (€)",
  viestiValinnainen: "Message (optional)",
  lahetaTarjousPainike: "Send offer",
  tarjousLahetetty: "Offer sent. The contact person will be in touch.",
  tarjousEpaonnistui: "Couldn't send the offer. Check the details and try again.",

  // Listing page — similar units, errors, locale toggle
  vastaaviaAsuntoja: "Similar homes",
  asuntoaEiLoytynyt: "Home not found.",
  asunnonLataaminenEpaonnistui: "This home's details couldn't be loaded right now.",
  takaisinHakuun: "Back to search",
  inEnglish: "In English",
  suomeksi: "Suomeksi",
};

export const ASUMISMUOTO_LABELS_EN: Record<HousingForm, string> = {
  vapaarahoitteinen: "Free-financed",
  lyhyt_korkotuki: "Short interest-subsidy",
  tarveharkintainen: "Needs-assessed",
  asumisoikeus: "Right-of-occupancy",
};

export const AVAILABILITY_LABELS_EN: Record<Availability, string> = {
  vapaa: "Vacant",
  vapautuu: "Becoming vacant",
  sopimuksella: "By arrangement",
};

export const LISTING_TYPE_LABELS_EN: Record<ListingType, string> = {
  vuokra: tekstitEn.vuokrattavat,
  myynti: tekstitEn.myytavat,
};

/**
 * Maps a decision's `puuttuva_tieto` evidence value (the rule engine's own
 * vocabulary, api/rules/*.py) to the Hakemus form section id it belongs to
 * (see the `id=` attributes in components/HakemusForm.tsx), so a
 * `puuttuvat_tiedot` decision row can link back to the exact field (spec
 * section 7, screen 4).
 *
 * There is no API field naming these two vocabularies as the same thing —
 * `puuttuva_tieto` values are evidence, not the RequiredField enum GET
 * /required-fields uses — so this mapping is read directly off every rule
 * module's `evidence={"puuttuva_tieto": ...}` literal as of 2026-09-14.
 * "tietojen_vahvistus" (an expired application asking to reconfirm) names no
 * single field, so it maps to nothing and the link falls back to the form's
 * top.
 */
const FIELD_BY_MISSING_INFO: Record<string, string> = {
  asumisoikeusnumero: "order_number",
  ruokakunnan_varallisuus: "assets",
  syntymavuodet: "household_size",
  ruokakunnan_bruttotulot: "household_income",
  ruokakunnan_jasenet: "household_size",
  asunnontarve: "housing_need",
  vakuuden_hyvaksyminen: "deposit_acknowledged",
  luottotiedot: "credit_record",
};

/** Given a decision's evidence list, the Hakemus section id it should link to, if any. */
export function fieldIdForEvidence(evidence: { avain: string; arvo: unknown }[]): string | null {
  const item = evidence.find((e) => e.avain === "puuttuva_tieto");
  if (!item || typeof item.arvo !== "string") return null;
  return FIELD_BY_MISSING_INFO[item.arvo] ?? null;
}

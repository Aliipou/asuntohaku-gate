/**
 * Typed fetch client for asuntohaku-gate's API (see ../../asuntohaku-gate-SPEC.md
 * section 6 and api/app/schemas.py).
 *
 * IMPORTANT: money fields are Python `Decimal`s and serialise to JSON *strings*
 * ("895.00"), never numbers — see the module docstring in api/app/schemas.py.
 * They are typed as `string` here on purpose. Parse with `Number(...)` only for
 * sorting/comparison; use `lib/format.ts` to display them so precision and
 * Finnish formatting stay in one place.
 */

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000").replace(
  /\/$/,
  "",
);

// ---------------------------------------------------------------------------
// Shared literal types (api/app/schemas.py)
// ---------------------------------------------------------------------------

export type OutcomeValue = "kelpoinen" | "puuttuvat_tiedot" | "ei_kelpoinen";
export type HousingForm =
  | "vapaarahoitteinen"
  | "lyhyt_korkotuki"
  | "tarveharkintainen"
  | "asumisoikeus";
export type ListingType = "vuokra" | "myynti";
export type Availability = "vapaa" | "vapautuu" | "sopimuksella";
export type MemberRole = "paahakija" | "toinen" | "muu";
export type NeedSituation = "asunnoton" | "irtisanottu" | "ahtaasti" | "ei_tarvetta";

// ---------------------------------------------------------------------------
// Units
// ---------------------------------------------------------------------------

export interface UnitOut {
  id: number;
  label: string;
  property_name: string;
  street: string;
  postal_code: string;
  city: string;
  built_year: number;
  housing_form: HousingForm;
  housing_form_label_fi: string;
  unit_number: string;
  rooms: number;
  floor: number;
  /** Decimal as string, e.g. "54.50". Use formatArea() to display. */
  area_m2: string;
  listing_type: ListingType;
  /** Non-null exactly when listing_type === 'vuokra'. Decimal as string. */
  rent_eur: string | null;
  /** Non-null exactly when listing_type === 'myynti'. Decimal as string. */
  price_eur: string | null;
  deposit_eur: string | null;
  availability: Availability;
  available_from: string | null;

  /**
   * NOT present in api/app/schemas.py::UnitOut as of this writing. The result
   * card metadata line ("2h + kk + s · 54,5 m² · 3. krs") needs a written
   * room layout, and the sale-row facts need a maintenance fee, but api/ is
   * being edited concurrently by another process and neither field has
   * landed in the search response yet. Typed optional so the UI already
   * degrades (see components/UnitRow.tsx) and picks up real values the
   * moment the backend adds them, without another frontend change.
   */
  room_layout_fi?: string;
  /** See room_layout_fi comment above — same situation, sale units only. */
  maintenance_fee_eur?: string | null;
}

export interface UnitDetailOut extends UnitOut {
  housing_form_explanation_fi: string;
  description_fi: string;
  description_en: string | null;
}

export interface UnitSearchOut {
  total: number;
  units: UnitOut[];
  cached: boolean;
}

/** Mirrors the query parameters accepted by GET /api/units (api/app/routers/units.py). */
export interface UnitSearchParams {
  city?: string;
  housing_form?: HousingForm;
  listing_type?: ListingType;
  availability?: Availability;
  rooms_min?: number;
  rooms_max?: number;
  rent_min?: number;
  rent_max?: number;
  price_min?: number;
  price_max?: number;
  limit?: number;
  offset?: number;
}

// ---------------------------------------------------------------------------
// Decisions / adaptive form
// ---------------------------------------------------------------------------

export interface EvidenceItem {
  avain: string;
  arvo: unknown;
  teksti: string;
}

export interface RuleOutcomeOut {
  rule_id: string;
  rule_title_fi: string;
  outcome: OutcomeValue;
  outcome_label_fi: string;
  message_fi: string;
  evidence: EvidenceItem[];
}

export interface DecisionOut {
  unit_id: number;
  unit_label: string;
  housing_form: HousingForm;
  outcome: OutcomeValue;
  outcome_label_fi: string;
  deciding_rule_id: string;
  message_fi: string;
  evidence: EvidenceItem[];
  rules: RuleOutcomeOut[];
}

export interface FieldCauseOut {
  unit_id: number;
  unit_label: string;
  rule_id: string;
  rule_title_fi: string;
}

export interface RequiredFieldOut {
  field: string;
  label_fi: string;
  required_by: FieldCauseOut[];
}

// ---------------------------------------------------------------------------
// Applications
// ---------------------------------------------------------------------------

export interface MemberIn {
  role?: MemberRole;
  birth_year?: number | null;
  gross_monthly_income_eur?: string | null;
  assets_eur?: string | null;
}

export interface MemberOut extends MemberIn {
  id: number;
}

export interface HousingNeedIn {
  situation: NeedSituation;
  urgency_note?: string | null;
}

export interface ApplicationCreate {
  contact_name?: string | null;
  contact_email?: string | null;
  contact_phone?: string | null;
}

export interface ApplicationUpdate {
  contact_name?: string | null;
  contact_email?: string | null;
  contact_phone?: string | null;
  order_number?: string | null;
  deposit_acknowledged?: boolean | null;
  credit_default_flag?: boolean | null;
  members?: MemberIn[] | null;
  housing_need?: HousingNeedIn | null;
}

export interface ApplicationUnitOut {
  unit_id: number;
  unit_label: string;
  housing_form: HousingForm;
  preference_rank: number;
}

export interface ApplicationOut {
  edit_token: string;
  status: string;
  created_at: string;
  expires_at: string;
  expired: boolean;
  contact_name: string | null;
  contact_email: string | null;
  contact_phone: string | null;
  order_number: string | null;
  deposit_acknowledged: boolean | null;
  credit_default_flag: boolean | null;
  members: MemberOut[];
  housing_need: HousingNeedIn | null;
  units: ApplicationUnitOut[];
}

export interface AddUnitIn {
  unit_id: number;
  preference_rank?: number;
}

// ---------------------------------------------------------------------------
// Viewings, offers, admin ranking
// ---------------------------------------------------------------------------

export interface ViewingOut {
  id: number;
  unit_id: number;
  starts_at: string;
  capacity: number;
  booked: number;
  seats_left: number;
}

export interface BookingIn {
  edit_token: string;
}

export interface BookingOut {
  id: number;
  viewing_id: number;
  created_at: string;
}

export interface OfferIn {
  contact_name: string;
  contact_email: string;
  amount_eur: string;
  message?: string | null;
}

export interface OfferOut {
  id: number;
  unit_id: number;
  contact_name: string;
  amount_eur: string;
  created_at: string;
}

export interface RankedApplicantOut {
  rank: number;
  application_id: number;
  contact_name: string | null;
  rule_id: string;
  message_fi: string;
  evidence: EvidenceItem[];
  eligibility: OutcomeValue;
  eligibility_message_fi: string;
}

export interface ApplicantRankingOut {
  unit_id: number;
  unit_label: string;
  housing_form: HousingForm;
  ranking_rule_id: string | null;
  ranking_basis_fi: string | null;
  applicants: RankedApplicantOut[];
}

export interface ErrorOut {
  detail: string;
  message_fi: string;
}

export interface FavouriteOut {
  unit_id: number;
  created_at: string;
}

export interface SavedSearchOut {
  id: number;
  name: string;
  query_json: Record<string, unknown>;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Fetch plumbing
// ---------------------------------------------------------------------------

export class ApiError extends Error {
  readonly status: number;
  readonly messageFi?: string;

  constructor(status: number, message: string, messageFi?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.messageFi = messageFi;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  let response: Response;
  try {
    response = await fetch(url, {
      cache: "no-store",
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    });
  } catch (cause) {
    throw new ApiError(
      0,
      `Verkkoyhteys API:iin (${url}) epäonnistui: ${cause instanceof Error ? cause.message : String(cause)}`,
    );
  }

  if (!response.ok) {
    let detail = response.statusText || `HTTP ${response.status}`;
    let messageFi: string | undefined;
    try {
      const body = (await response.json()) as Partial<ErrorOut>;
      detail = body.detail ?? detail;
      messageFi = body.message_fi;
    } catch {
      // Response body wasn't JSON (or was empty) — keep the status text.
    }
    throw new ApiError(response.status, detail, messageFi);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

function query(params: object): string {
  const qs = new URLSearchParams();
  for (const [key, value] of Object.entries(params as Record<string, unknown>)) {
    if (value !== undefined && value !== null && value !== "") {
      qs.set(key, String(value));
    }
  }
  const s = qs.toString();
  return s ? `?${s}` : "";
}

// ---------------------------------------------------------------------------
// Endpoints (asuntohaku-gate-SPEC.md section 6)
// ---------------------------------------------------------------------------

export function searchUnits(params: UnitSearchParams = {}): Promise<UnitSearchOut> {
  return request<UnitSearchOut>(`/api/units${query(params)}`);
}

export function getUnit(id: number): Promise<UnitDetailOut> {
  return request<UnitDetailOut>(`/api/units/${id}`);
}

export function getSimilarUnits(id: number): Promise<UnitOut[]> {
  return request<UnitOut[]>(`/api/units/${id}/similar`);
}

export function getUnitViewings(unitId: number): Promise<ViewingOut[]> {
  return request<ViewingOut[]>(`/api/units/${unitId}/viewings`);
}

export function bookViewing(viewingId: number, payload: BookingIn): Promise<BookingOut> {
  return request<BookingOut>(`/api/viewings/${viewingId}/bookings`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function createOffer(unitId: number, payload: OfferIn): Promise<OfferOut> {
  return request<OfferOut>(`/api/units/${unitId}/offers`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getCities(): Promise<string[]> {
  return request<string[]>("/api/cities");
}

export function createApplication(payload: ApplicationCreate = {}): Promise<ApplicationOut> {
  return request<ApplicationOut>("/api/applications", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getApplication(token: string): Promise<ApplicationOut> {
  return request<ApplicationOut>(`/api/applications/${token}`);
}

export function updateApplication(
  token: string,
  payload: ApplicationUpdate,
): Promise<ApplicationOut> {
  return request<ApplicationOut>(`/api/applications/${token}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function addApplicationUnit(token: string, payload: AddUnitIn): Promise<ApplicationOut> {
  return request<ApplicationOut>(`/api/applications/${token}/units`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function removeApplicationUnit(token: string, unitId: number): Promise<ApplicationOut> {
  return request<ApplicationOut>(`/api/applications/${token}/units/${unitId}`, {
    method: "DELETE",
  });
}

export function getRequiredFields(token: string): Promise<RequiredFieldOut[]> {
  return request<RequiredFieldOut[]>(`/api/applications/${token}/required-fields`);
}

export function getDecisions(token: string): Promise<DecisionOut[]> {
  return request<DecisionOut[]>(`/api/applications/${token}/decisions`);
}

export function getFavourites(sessionKey: string): Promise<FavouriteOut[]> {
  return request<FavouriteOut[]>(`/api/favourites${query({ session_key: sessionKey })}`);
}

export function addFavourite(sessionKey: string, unitId: number): Promise<FavouriteOut> {
  return request<FavouriteOut>("/api/favourites", {
    method: "POST",
    body: JSON.stringify({ session_key: sessionKey, unit_id: unitId }),
  });
}

export function removeFavourite(sessionKey: string, unitId: number): Promise<void> {
  return request<void>(`/api/favourites/${unitId}${query({ session_key: sessionKey })}`, {
    method: "DELETE",
  });
}

export function getSavedSearches(sessionKey: string): Promise<SavedSearchOut[]> {
  return request<SavedSearchOut[]>(`/api/saved-searches${query({ session_key: sessionKey })}`);
}

export function createSavedSearch(
  sessionKey: string,
  name: string,
  queryJson: Record<string, unknown>,
): Promise<SavedSearchOut> {
  return request<SavedSearchOut>("/api/saved-searches", {
    method: "POST",
    body: JSON.stringify({ session_key: sessionKey, name, query_json: queryJson }),
  });
}

export function getRankedApplicants(unitId: number): Promise<ApplicantRankingOut> {
  return request<ApplicantRankingOut>(`/api/admin/units/${unitId}/applicants`);
}

/**
 * Search-filter state, encoded in and decoded from the URL.
 *
 * asuntohaku-gate-SPEC.md section 7 requires filter state to live in the URL
 * so that a filtered search is a shareable, reloadable link. This module is
 * the one place that translates between "what the URL says" and "what the
 * search form and the API need", so app/page.tsx and the filter form never
 * hand-roll query-string parsing themselves.
 */

import type { Availability, HousingForm, ListingType, UnitOut, UnitSearchParams } from "./api";

export type SortOrder = "uusimmat" | "halvin" | "kallein" | "suurin";

export interface SearchFilters {
  listingType: ListingType;
  city?: string;
  housingForm?: HousingForm;
  availability?: Availability;
  roomsMin?: number;
  roomsMax?: number;
  /**
   * A single "price range" concept in the UI. Means rent (€/kk) when
   * listingType is 'vuokra' and purchase price (€) when it is 'myynti' — see
   * toApiSearchParams(), which is where that split actually happens.
   */
  priceMin?: number;
  priceMax?: number;
  sort: SortOrder;
}

const LISTING_TYPES: readonly ListingType[] = ["vuokra", "myynti"];
const HOUSING_FORMS: readonly HousingForm[] = [
  "vapaarahoitteinen",
  "lyhyt_korkotuki",
  "tarveharkintainen",
  "asumisoikeus",
];
const AVAILABILITIES: readonly Availability[] = ["vapaa", "vapautuu", "sopimuksella"];
const SORT_ORDERS: readonly SortOrder[] = ["uusimmat", "halvin", "kallein", "suurin"];

export const DEFAULT_FILTERS: SearchFilters = {
  listingType: "vuokra",
  sort: "uusimmat",
};

/** What Next.js hands a Server Component's page as `searchParams` (already awaited). */
export type RawSearchParams = Record<string, string | string[] | undefined>;

function readParam(params: URLSearchParams | RawSearchParams, key: string): string | undefined {
  if (params instanceof URLSearchParams) {
    return params.get(key) ?? undefined;
  }
  const value = params[key];
  return Array.isArray(value) ? value[0] : value;
}

function parseEnum<T extends string>(
  raw: string | undefined,
  allowed: readonly T[],
): T | undefined {
  return raw !== undefined && (allowed as readonly string[]).includes(raw) ? (raw as T) : undefined;
}

function parsePositiveInt(raw: string | undefined): number | undefined {
  if (raw === undefined) return undefined;
  const n = Number.parseInt(raw, 10);
  return Number.isInteger(n) && n > 0 ? n : undefined;
}

function parseNonNegativeNumber(raw: string | undefined): number | undefined {
  if (raw === undefined) return undefined;
  const n = Number(raw);
  return Number.isFinite(n) && n >= 0 ? n : undefined;
}

/**
 * Reads filter state out of a URL's query string. Unknown, malformed or
 * out-of-range values are silently dropped in favour of the default rather
 * than thrown — a hand-edited or stale shared link should degrade to "show
 * everything", never crash the page.
 */
export function parseSearchFilters(params: URLSearchParams | RawSearchParams): SearchFilters {
  const city = readParam(params, "city");
  return {
    listingType:
      parseEnum(readParam(params, "listing_type"), LISTING_TYPES) ?? DEFAULT_FILTERS.listingType,
    city: city ? city : undefined,
    housingForm: parseEnum(readParam(params, "housing_form"), HOUSING_FORMS),
    availability: parseEnum(readParam(params, "availability"), AVAILABILITIES),
    roomsMin: parsePositiveInt(readParam(params, "rooms_min")),
    roomsMax: parsePositiveInt(readParam(params, "rooms_max")),
    priceMin: parseNonNegativeNumber(readParam(params, "price_min")),
    priceMax: parseNonNegativeNumber(readParam(params, "price_max")),
    sort: parseEnum(readParam(params, "sort"), SORT_ORDERS) ?? DEFAULT_FILTERS.sort,
  };
}

/**
 * Encodes filter state back into a query string, omitting anything equal to
 * the default so a plain, unfiltered search produces a clean URL ("/" rather
 * than "/?listing_type=vuokra&sort=uusimmat").
 */
export function filtersToSearchParams(filters: SearchFilters): URLSearchParams {
  const params = new URLSearchParams();
  if (filters.listingType !== DEFAULT_FILTERS.listingType) {
    params.set("listing_type", filters.listingType);
  }
  if (filters.city) params.set("city", filters.city);
  if (filters.housingForm) params.set("housing_form", filters.housingForm);
  if (filters.availability) params.set("availability", filters.availability);
  if (filters.roomsMin !== undefined) params.set("rooms_min", String(filters.roomsMin));
  if (filters.roomsMax !== undefined) params.set("rooms_max", String(filters.roomsMax));
  if (filters.priceMin !== undefined) params.set("price_min", String(filters.priceMin));
  if (filters.priceMax !== undefined) params.set("price_max", String(filters.priceMax));
  if (filters.sort !== DEFAULT_FILTERS.sort) params.set("sort", filters.sort);
  return params;
}

/**
 * Maps UI filter state onto GET /api/units's actual query parameters
 * (api/app/routers/units.py). The UI has one price-range concept; the API
 * has separate rent_min/rent_max and price_min/price_max because a rental
 * row's price is a recurring rent and a sale row's is a purchase price.
 */
export function toApiSearchParams(filters: SearchFilters): UnitSearchParams {
  const out: UnitSearchParams = { listing_type: filters.listingType };
  if (filters.city) out.city = filters.city;
  if (filters.housingForm) out.housing_form = filters.housingForm;
  if (filters.availability) out.availability = filters.availability;
  if (filters.roomsMin !== undefined) out.rooms_min = filters.roomsMin;
  if (filters.roomsMax !== undefined) out.rooms_max = filters.roomsMax;
  if (filters.listingType === "myynti") {
    if (filters.priceMin !== undefined) out.price_min = filters.priceMin;
    if (filters.priceMax !== undefined) out.price_max = filters.priceMax;
  } else {
    if (filters.priceMin !== undefined) out.rent_min = filters.priceMin;
    if (filters.priceMax !== undefined) out.rent_max = filters.priceMax;
  }
  return out;
}

/**
 * Client-side sort for the four sort orders the search page offers.
 *
 * GET /api/units (api/app/routers/units.py) does not currently accept a
 * `sort` parameter, even though spec section 6 says search "accepts the sort
 * order the UI offers". Rather than block the search page on that endpoint
 * gaining a parameter — api/ is being edited by a concurrent process — the
 * page fetches unsorted and orders the page of results itself. "uusimmat"
 * (newest first) uses descending `id` as a stand-in for recency, since
 * UnitOut carries no created_at/listed_at field to sort on; swap this for a
 * real timestamp field the moment one exists.
 */
export function sortUnits<T extends Pick<UnitOut, "id" | "area_m2" | "rent_eur" | "price_eur">>(
  units: readonly T[],
  sort: SortOrder,
): T[] {
  const priceOf = (u: T) => Number(u.rent_eur ?? u.price_eur ?? "0");
  const sorted = [...units];
  switch (sort) {
    case "halvin":
      sorted.sort((a, b) => priceOf(a) - priceOf(b));
      break;
    case "kallein":
      sorted.sort((a, b) => priceOf(b) - priceOf(a));
      break;
    case "suurin":
      sorted.sort((a, b) => Number(b.area_m2) - Number(a.area_m2));
      break;
    case "uusimmat":
      sorted.sort((a, b) => b.id - a.id);
      break;
  }
  return sorted;
}

import { describe, expect, it } from "vitest";
import {
  DEFAULT_FILTERS,
  filtersToSearchParams,
  parseSearchFilters,
  sortUnits,
  toApiSearchParams,
  type SearchFilters,
} from "./filters";

describe("parseSearchFilters", () => {
  it("falls back to the default listing type and sort order when the URL carries none", () => {
    expect(parseSearchFilters(new URLSearchParams(""))).toEqual(DEFAULT_FILTERS);
  });

  it("reads every recognised query parameter", () => {
    const params = new URLSearchParams(
      "listing_type=myynti&city=Tampere&housing_form=tarveharkintainen&availability=vapaa" +
        "&rooms_min=2&rooms_max=4&price_min=500&price_max=1500&sort=suurin",
    );
    expect(parseSearchFilters(params)).toEqual({
      listingType: "myynti",
      city: "Tampere",
      housingForm: "tarveharkintainen",
      availability: "vapaa",
      roomsMin: 2,
      roomsMax: 4,
      priceMin: 500,
      priceMax: 1500,
      sort: "suurin",
    } satisfies SearchFilters);
  });

  it("also accepts the plain object shape Next.js hands a page's searchParams prop", () => {
    expect(parseSearchFilters({ city: "Espoo", rooms_min: "3" })).toMatchObject({
      city: "Espoo",
      roomsMin: 3,
    });
  });

  it("drops unrecognised, malformed or hostile values instead of crashing or trusting them", () => {
    const params = new URLSearchParams("listing_type=hovercraft&rooms_min=-3&sort=DROP TABLE&city=");
    const filters = parseSearchFilters(params);
    expect(filters.listingType).toBe("vuokra");
    expect(filters.roomsMin).toBeUndefined();
    expect(filters.sort).toBe("uusimmat");
    expect(filters.city).toBeUndefined();
  });

  it("treats a repeated query parameter the way Next.js delivers it: takes the first value", () => {
    expect(parseSearchFilters({ city: ["Helsinki", "Vantaa"] })).toMatchObject({ city: "Helsinki" });
  });
});

describe("filtersToSearchParams", () => {
  it("round-trips through parseSearchFilters for a fully specified filter set", () => {
    const filters: SearchFilters = {
      listingType: "myynti",
      city: "Espoo",
      housingForm: "asumisoikeus",
      availability: "vapautuu",
      roomsMin: 1,
      roomsMax: 3,
      priceMin: 100000,
      priceMax: 250000,
      sort: "halvin",
    };
    expect(parseSearchFilters(filtersToSearchParams(filters))).toEqual(filters);
  });

  it("omits default values so an unfiltered search stays a clean, shareable URL", () => {
    expect(filtersToSearchParams(DEFAULT_FILTERS).toString()).toBe("");
  });

  it("only encodes the filters actually set, in a stable and inspectable form", () => {
    const params = filtersToSearchParams({ ...DEFAULT_FILTERS, city: "Helsinki", roomsMin: 2 });
    expect(params.get("city")).toBe("Helsinki");
    expect(params.get("rooms_min")).toBe("2");
    expect(params.has("listing_type")).toBe(false);
  });
});

describe("toApiSearchParams", () => {
  it("maps the UI price range onto rent_min/rent_max for rental stock", () => {
    expect(toApiSearchParams({ ...DEFAULT_FILTERS, priceMin: 500, priceMax: 900 })).toMatchObject({
      listing_type: "vuokra",
      rent_min: 500,
      rent_max: 900,
    });
  });

  it("maps the same price range onto price_min/price_max for sale stock", () => {
    const result = toApiSearchParams({
      ...DEFAULT_FILTERS,
      listingType: "myynti",
      priceMin: 150000,
      priceMax: 300000,
    });
    expect(result).toMatchObject({ listing_type: "myynti", price_min: 150000, price_max: 300000 });
    expect(result.rent_min).toBeUndefined();
    expect(result.rent_max).toBeUndefined();
  });
});

describe("sortUnits", () => {
  const units = [
    { id: 1, area_m2: "40.0", rent_eur: "900.00", price_eur: null },
    { id: 3, area_m2: "65.5", rent_eur: "1200.00", price_eur: null },
    { id: 2, area_m2: "52.0", rent_eur: "700.00", price_eur: null },
  ];

  it("orders cheapest first for 'halvin'", () => {
    expect(sortUnits(units, "halvin").map((u) => u.id)).toEqual([2, 1, 3]);
  });

  it("orders most expensive first for 'kallein'", () => {
    expect(sortUnits(units, "kallein").map((u) => u.id)).toEqual([3, 1, 2]);
  });

  it("orders the largest floor area first for 'suurin'", () => {
    expect(sortUnits(units, "suurin").map((u) => u.id)).toEqual([3, 2, 1]);
  });

  it("orders by descending id for 'uusimmat', as a stand-in for a missing recency field", () => {
    expect(sortUnits(units, "uusimmat").map((u) => u.id)).toEqual([3, 2, 1]);
  });

  it("does not mutate the input array", () => {
    const copy = [...units];
    sortUnits(units, "halvin");
    expect(units).toEqual(copy);
  });
});

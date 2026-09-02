"use client";

import { useState, type ChangeEvent, type FormEvent } from "react";
import Link from "next/link";
import type { SearchFilters } from "@/lib/filters";
import { ASUMISMUOTO_LABELS, AVAILABILITY_LABELS, tekstit } from "@/lib/tekstit";
import type { Availability, HousingForm, ListingType } from "@/lib/api";

/** Auto-submits the enclosing <form> so every control change re-encodes the URL. */
function autoSubmit(e: ChangeEvent<HTMLInputElement | HTMLSelectElement>) {
  e.currentTarget.form?.requestSubmit();
}

const ROOM_OPTIONS = [1, 2, 3, 4, 5];

export function SearchControls({
  filters,
  cities,
  total,
}: {
  filters: SearchFilters;
  cities: string[];
  /** null when the search request failed — the count is then not shown. */
  total: number | null;
}) {
  const [tallennettu, setTallennettu] = useState(false);
  const advancedOpen = Boolean(filters.housingForm || filters.availability);
  const priceLabel = filters.listingType === "myynti" ? tekstit.hintaMyyntiLabel : tekstit.hintaVuokraLabel;

  function onSubmit(e: FormEvent<HTMLFormElement>) {
    // Empty text/number inputs would otherwise land in the URL as "city=" —
    // strip them so the resulting link stays clean (filtersToSearchParams
    // does the equivalent trimming for state built up in code).
    const form = e.currentTarget;
    for (const el of Array.from(form.elements)) {
      const isEmptyTextInput = el instanceof HTMLInputElement && el.type !== "radio" && el.value === "";
      const isEmptySelect = el instanceof HTMLSelectElement && el.value === "";
      if (isEmptyTextInput || isEmptySelect) {
        el.disabled = true;
      }
    }
  }

  return (
    <form
      method="GET"
      action="/"
      onSubmit={onSubmit}
      className="flex flex-col gap-4 border-b border-line pb-5"
    >
      <div
        role="radiogroup"
        aria-label={tekstit.valitseVuokraTaiMyynti}
        className="inline-flex w-fit rounded-full border border-line bg-paper-raised p-1"
      >
        {(["vuokra", "myynti"] as ListingType[]).map((value) => (
          <label
            key={value}
            className="relative cursor-pointer rounded-full px-4 py-1.5 text-sm font-medium text-ink-muted has-checked:bg-accent has-checked:text-accent-ink"
          >
            <input
              type="radio"
              name="listing_type"
              value={value}
              defaultChecked={filters.listingType === value}
              onChange={autoSubmit}
              className="sr-only"
            />
            {value === "vuokra" ? tekstit.vuokrattavat : tekstit.myytavat}
          </label>
        ))}
      </div>

      <div className="flex flex-wrap items-end gap-3">
        <label className="flex flex-col gap-1 text-sm">
          <span className="font-medium text-ink">{tekstit.kaupunki}</span>
          <input
            type="text"
            name="city"
            list="kaupunki-lista"
            defaultValue={filters.city ?? ""}
            placeholder={tekstit.kaupunkiPlaceholder}
            onBlur={(e) => e.currentTarget.form?.requestSubmit()}
            className="w-40 rounded-md border border-line bg-paper-raised px-3 py-1.5 text-ink outline-none focus-visible:border-accent"
          />
          <datalist id="kaupunki-lista">
            {cities.map((city) => (
              <option key={city} value={city} />
            ))}
          </datalist>
        </label>

        <fieldset className="flex flex-col gap-1 text-sm">
          <legend className="font-medium text-ink">{tekstit.huoneet}</legend>
          <div className="flex items-center gap-1.5">
            <select
              name="rooms_min"
              defaultValue={filters.roomsMin ?? ""}
              onChange={autoSubmit}
              aria-label={tekstit.huoneitaVahintaan}
              className="rounded-md border border-line bg-paper-raised px-2 py-1.5 text-ink outline-none focus-visible:border-accent"
            >
              <option value="">{tekstit.kaikki}</option>
              {ROOM_OPTIONS.map((n) => (
                <option key={n} value={n}>
                  {n}+
                </option>
              ))}
            </select>
            <span aria-hidden="true" className="text-ink-muted">
              –
            </span>
            <select
              name="rooms_max"
              defaultValue={filters.roomsMax ?? ""}
              onChange={autoSubmit}
              aria-label={tekstit.huoneitaEnintaan}
              className="rounded-md border border-line bg-paper-raised px-2 py-1.5 text-ink outline-none focus-visible:border-accent"
            >
              <option value="">{tekstit.kaikki}</option>
              {ROOM_OPTIONS.map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </div>
        </fieldset>

        <fieldset className="flex flex-col gap-1 text-sm">
          <legend className="font-medium text-ink">{priceLabel}</legend>
          <div className="flex items-center gap-1.5">
            <input
              type="number"
              inputMode="numeric"
              min={0}
              step={filters.listingType === "myynti" ? 5000 : 50}
              name="price_min"
              defaultValue={filters.priceMin ?? ""}
              placeholder={tekstit.hintaAlkaen}
              aria-label={tekstit.hintaAlkaen}
              onBlur={(e) => e.currentTarget.form?.requestSubmit()}
              className="w-24 rounded-md border border-line bg-paper-raised px-2 py-1.5 text-ink outline-none focus-visible:border-accent"
            />
            <span aria-hidden="true" className="text-ink-muted">
              –
            </span>
            <input
              type="number"
              inputMode="numeric"
              min={0}
              step={filters.listingType === "myynti" ? 5000 : 50}
              name="price_max"
              defaultValue={filters.priceMax ?? ""}
              placeholder={tekstit.hintaEnintaan}
              aria-label={tekstit.hintaEnintaan}
              onBlur={(e) => e.currentTarget.form?.requestSubmit()}
              className="w-24 rounded-md border border-line bg-paper-raised px-2 py-1.5 text-ink outline-none focus-visible:border-accent"
            />
          </div>
        </fieldset>

        <button
          type="submit"
          className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-accent-ink hover:opacity-90"
        >
          {tekstit.hae}
        </button>

        <Link href="/" className="text-sm text-ink-muted underline-offset-2 hover:underline">
          {tekstit.nollaaHakuehdot}
        </Link>
      </div>

      <details open={advancedOpen} className="text-sm">
        <summary className="w-fit cursor-pointer select-none font-medium text-accent">
          {tekstit.lisaaHakuehtoja}
        </summary>
        <div className="mt-3 flex flex-wrap gap-3">
          <label className="flex flex-col gap-1">
            <span className="font-medium text-ink">{tekstit.asumismuoto}</span>
            <select
              name="housing_form"
              defaultValue={filters.housingForm ?? ""}
              onChange={autoSubmit}
              className="rounded-md border border-line bg-paper-raised px-2 py-1.5 text-ink outline-none focus-visible:border-accent"
            >
              <option value="">{tekstit.kaikki}</option>
              {(Object.keys(ASUMISMUOTO_LABELS) as HousingForm[]).map((form) => (
                <option key={form} value={form}>
                  {ASUMISMUOTO_LABELS[form]}
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-1">
            <span className="font-medium text-ink">{tekstit.vapautuminen}</span>
            <select
              name="availability"
              defaultValue={filters.availability ?? ""}
              onChange={autoSubmit}
              className="rounded-md border border-line bg-paper-raised px-2 py-1.5 text-ink outline-none focus-visible:border-accent"
            >
              <option value="">{tekstit.kaikki}</option>
              {(Object.keys(AVAILABILITY_LABELS) as Availability[]).map((value) => (
                <option key={value} value={value}>
                  {AVAILABILITY_LABELS[value]}
                </option>
              ))}
            </select>
          </label>
        </div>
      </details>

      <div className="flex flex-wrap items-center justify-between gap-3 pt-1">
        <p aria-live="polite" className="tabular-nums text-sm text-ink-muted">
          {total !== null ? tekstit.tulosMaara(total) : null}
        </p>

        <div className="flex items-center gap-3">
          <button
            type="button"
            aria-pressed={tallennettu}
            onClick={() => setTallennettu((v) => !v)}
            className="text-sm font-medium text-accent hover:underline"
          >
            {tallennettu ? tekstit.hakuTallennettu : tekstit.tallennaHaku}
          </button>

          <label className="flex items-center gap-2 text-sm">
            <span className="font-medium text-ink">{tekstit.jarjestys}</span>
            <select
              name="sort"
              defaultValue={filters.sort}
              onChange={autoSubmit}
              className="rounded-md border border-line bg-paper-raised px-2 py-1.5 text-ink outline-none focus-visible:border-accent"
            >
              <option value="uusimmat">{tekstit.uusimmat}</option>
              <option value="halvin">{tekstit.halvinEnsin}</option>
              <option value="kallein">{tekstit.kalleinEnsin}</option>
              <option value="suurin">{tekstit.suurinPintaAla}</option>
            </select>
          </label>
        </div>
      </div>
    </form>
  );
}

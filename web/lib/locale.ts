/**
 * The English locale is scoped to the search and detail pages only (SPEC
 * section 7) — this module is the one place that resolves `?lang=` and picks
 * between lib/tekstit.ts and its English mirror. No other screen imports it.
 */

import {
  ASUMISMUOTO_LABELS_EN,
  AVAILABILITY_LABELS_EN,
  LISTING_TYPE_LABELS_EN,
  tekstitEn,
} from "./tekstit.en";
import { ASUMISMUOTO_LABELS, AVAILABILITY_LABELS, LISTING_TYPE_LABELS, tekstit } from "./tekstit";

export type Locale = "fi" | "en";

export function parseLocale(raw: string | string[] | undefined): Locale {
  const value = Array.isArray(raw) ? raw[0] : raw;
  return value === "en" ? "en" : "fi";
}

export function pickTekstit(locale: Locale): typeof tekstit {
  return locale === "en" ? tekstitEn : tekstit;
}

export function pickAsumismuotoLabels(locale: Locale) {
  return locale === "en" ? ASUMISMUOTO_LABELS_EN : ASUMISMUOTO_LABELS;
}

export function pickAvailabilityLabels(locale: Locale) {
  return locale === "en" ? AVAILABILITY_LABELS_EN : AVAILABILITY_LABELS;
}

export function pickListingTypeLabels(locale: Locale) {
  return locale === "en" ? LISTING_TYPE_LABELS_EN : LISTING_TYPE_LABELS;
}

/** Appends/overrides `lang` on a query string built from the current filters. */
export function withLocale(params: URLSearchParams, locale: Locale): URLSearchParams {
  const next = new URLSearchParams(params);
  if (locale === "en") {
    next.set("lang", "en");
  } else {
    next.delete("lang");
  }
  return next;
}

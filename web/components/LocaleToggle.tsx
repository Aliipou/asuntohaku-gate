"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { withLocale, type Locale } from "@/lib/locale";
import type { tekstit } from "@/lib/tekstit";

/**
 * Switches `?lang=` on the current URL, keeping every other query parameter
 * (so toggling locale mid-search doesn't drop the filters already applied).
 * Only rendered on the search and detail pages — the two with a secondary
 * locale (spec section 7).
 */
export function LocaleToggle({ locale, t }: { locale: Locale; t: typeof tekstit }) {
  const searchParams = useSearchParams();
  const target: Locale = locale === "en" ? "fi" : "en";
  const href = `?${withLocale(new URLSearchParams(searchParams), target).toString()}`;

  return (
    <Link href={href} className="text-sm font-medium text-accent hover:underline">
      {target === "en" ? t.inEnglish : t.suomeksi}
    </Link>
  );
}

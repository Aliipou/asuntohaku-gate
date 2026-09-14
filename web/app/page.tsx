import { getCities, searchUnits, type CityOut, type UnitOut } from "@/lib/api";
import { parseSearchFilters, sortUnits, toApiSearchParams, type RawSearchParams } from "@/lib/filters";
import { parseLocale, pickTekstit } from "@/lib/locale";
import { SearchControls } from "@/components/SearchControls";
import { SearchResults } from "@/components/SearchResults";
import { LocaleToggle } from "@/components/LocaleToggle";

// searchParams makes this request-time (spec section 7: filter state lives in
// the URL), so there is nothing worth prerendering here.
export const dynamic = "force-dynamic";

interface SearchPageProps {
  searchParams: Promise<RawSearchParams>;
}

/**
 * Asuntohaku — the landing page *is* the search (spec section 7, screen 1).
 * No marketing hero: this route reads the URL's filter state, fetches the
 * matching units and renders the result list beside a map. The API is not
 * guaranteed to be running (this scaffold ships ahead of it), so a fetch
 * failure degrades to a plain message instead of a crashed page.
 *
 * `?lang=en` switches this page to English — the search and detail pages are
 * the only ones with a secondary locale (spec section 7); see lib/locale.ts.
 */
export default async function Page({ searchParams }: SearchPageProps) {
  const rawParams = await searchParams;
  const filters = parseSearchFilters(rawParams);
  const locale = parseLocale(rawParams.lang);
  const t = pickTekstit(locale);

  let cities: CityOut[] = [];
  let units: UnitOut[] = [];
  let total: number | null = null;
  let loadError = false;

  try {
    const [citiesResult, searchResult] = await Promise.all([
      getCities().catch(() => [] as CityOut[]),
      searchUnits({ ...toApiSearchParams(filters), limit: 48 }),
    ]);
    cities = citiesResult;
    units = sortUnits(searchResult.units, filters.sort);
    total = searchResult.total;
  } catch {
    loadError = true;
  }

  return (
    <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-5 px-4 py-6 sm:px-6">
      <div className="flex items-center justify-between gap-3">
        <h1 className="sr-only">{t.sivunOtsikko}</h1>
        <LocaleToggle locale={locale} t={t} />
      </div>

      <SearchControls filters={filters} cities={cities} total={loadError ? null : total} locale={locale} t={t} />

      {loadError ? (
        <p role="alert" className="rounded-md border border-line bg-paper-raised p-4 text-ink">
          {t.hakuEpaonnistui}
        </p>
      ) : (
        <SearchResults units={units} locale={locale} t={t} />
      )}
    </main>
  );
}

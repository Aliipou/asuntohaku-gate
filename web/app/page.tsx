import { getCities, searchUnits, type UnitOut } from "@/lib/api";
import { parseSearchFilters, sortUnits, toApiSearchParams, type RawSearchParams } from "@/lib/filters";
import { tekstit } from "@/lib/tekstit";
import { SearchControls } from "@/components/SearchControls";
import { UnitRow } from "@/components/UnitRow";

// searchParams makes this request-time (spec section 7: filter state lives in
// the URL), so there is nothing worth prerendering here.
export const dynamic = "force-dynamic";

interface SearchPageProps {
  searchParams: Promise<RawSearchParams>;
}

/**
 * Asuntohaku — the landing page *is* the search (spec section 7, screen 1).
 * No marketing hero: this route reads the URL's filter state, fetches the
 * matching units and renders the result list next to a placeholder for the
 * map. The API is not guaranteed to be running (this scaffold ships ahead of
 * it), so a fetch failure degrades to a plain Finnish message instead of a
 * crashed page.
 */
export default async function Page({ searchParams }: SearchPageProps) {
  const rawParams = await searchParams;
  const filters = parseSearchFilters(rawParams);

  let cities: string[] = [];
  let units: UnitOut[] = [];
  let total: number | null = null;
  let loadError = false;

  try {
    const [citiesResult, searchResult] = await Promise.all([
      getCities().catch(() => [] as string[]),
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
      <h1 className="sr-only">{tekstit.sivunOtsikko}</h1>

      <SearchControls filters={filters} cities={cities} total={loadError ? null : total} />

      {loadError ? (
        <p role="alert" className="rounded-md border border-line bg-paper-raised p-4 text-ink">
          {tekstit.hakuEpaonnistui}
        </p>
      ) : (
        <div className="grid flex-1 grid-cols-1 gap-5 lg:grid-cols-[minmax(0,1fr)_22rem]">
          <ol className="flex flex-col gap-3">
            {units.length === 0 ? (
              <li className="rounded-md border border-line bg-paper-raised p-4 text-ink-muted">
                {tekstit.eiTuloksia}
              </li>
            ) : (
              units.map((unit) => <UnitRow key={unit.id} unit={unit} />)
            )}
          </ol>

          {/*
            MAP PLACEHOLDER — spec section 7 wants a split view: result list
            beside a map with price pins, hovering a row highlighting its
            pin. Deliberately not built here: the task that scaffolds this
            app is explicit that MapLibre GL JS is not to be installed yet.
            Wire the real map into this div once that dependency lands.
          */}
          <div
            aria-hidden="true"
            className="hidden min-h-[24rem] flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-line bg-paper-raised p-6 text-center text-sm text-ink-muted lg:flex"
          >
            <p className="font-medium text-ink">{tekstit.kartta}</p>
            <p>{tekstit.karttaPlaceholder}</p>
          </div>
        </div>
      )}
    </main>
  );
}

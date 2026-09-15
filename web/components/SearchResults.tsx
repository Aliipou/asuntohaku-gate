"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import type { UnitOut } from "@/lib/api";
import { getFavourites } from "@/lib/api";
import { getSessionKey } from "@/lib/browserState";
import { formatEuros } from "@/lib/format";
import { pickTekstit, type Locale } from "@/lib/locale";
import { UnitRow } from "./UnitRow";
import { Map, type MapPoint } from "./Map";

/**
 * Screen 1's split view (spec section 7): a result list beside a map with
 * price pins, the two linked so hovering a row highlights its pin and vice
 * versa. A single `hoveredId` piece of state, lifted here, is the whole link.
 */
export function SearchResults({
  units,
  locale,
}: {
  units: UnitOut[];
  locale: Locale;
}) {
  const t = pickTekstit(locale);
  const router = useRouter();
  const [hoveredId, setHoveredId] = useState<number | null>(null);
  const [favouriteIds, setFavouriteIds] = useState<Set<number>>(new Set());
  const langSuffix = locale === "en" ? "?lang=en" : "";

  useEffect(() => {
    let cancelled = false;
    getFavourites(getSessionKey())
      .then((favourites) => {
        if (!cancelled) setFavouriteIds(new Set(favourites.map((u) => u.id)));
      })
      .catch(() => {
        // Favourites are a nice-to-have overlay on the search results; a
        // failed fetch just leaves every heart unfilled.
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const points = useMemo<MapPoint[]>(
    () =>
      units.map((unit) => {
        const price = unit.listing_type === "vuokra" ? unit.rent_eur : unit.price_eur;
        const label = price ? formatEuros(price) : t.eiTiedossa;
        return {
          id: unit.id,
          lat: Number(unit.lat),
          lng: Number(unit.lng),
          label,
          title: `${label} — ${unit.property_name} ${unit.unit_number}, ${unit.city}`,
        };
      }),
    [units, t],
  );

  return (
    <div className="grid flex-1 grid-cols-1 gap-5 lg:grid-cols-[minmax(0,1fr)_22rem]">
      <ol className="flex flex-col gap-3">
        {units.length === 0 ? (
          <li className="rounded-md border border-line bg-paper-raised p-4 text-ink-muted">
            {t.eiTuloksia}
          </li>
        ) : (
          units.map((unit) => (
            <UnitRow
              key={unit.id}
              unit={unit}
              href={`/asunnot/${unit.id}${langSuffix}`}
              t={t}
              active={hoveredId === unit.id}
              favourite={favouriteIds.has(unit.id)}
              onHover={setHoveredId}
            />
          ))
        )}
      </ol>

      <div className="hidden min-h-[24rem] overflow-hidden rounded-lg border border-line lg:block">
        <Map
          points={points}
          activeId={hoveredId}
          onHoverPoint={setHoveredId}
          onSelectPoint={(id) => router.push(`/asunnot/${id}${langSuffix}`)}
          className="h-full min-h-[24rem] w-full"
        />
      </div>
    </div>
  );
}

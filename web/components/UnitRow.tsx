"use client";

import { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { addFavourite, removeFavourite, type UnitOut } from "@/lib/api";
import { getSessionKey } from "@/lib/browserState";
import { formatArea, formatEuros } from "@/lib/format";
import { tekstit } from "@/lib/tekstit";

function HeartIcon({ filled }: { filled: boolean }) {
  return (
    <svg
      viewBox="0 0 24 24"
      width="20"
      height="20"
      aria-hidden="true"
      fill={filled ? "currentColor" : "none"}
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinejoin="round"
    >
      <path d="M12 20.2c-.3 0-.6-.1-.8-.3C7.8 17 3.5 13.4 3.5 9.3 3.5 6.4 5.7 4 8.6 4c1.5 0 2.9.7 3.4 1.8C12.5 4.7 13.9 4 15.4 4c2.9 0 5.1 2.4 5.1 5.3 0 4.1-4.3 7.7-7.7 10.6-.2.2-.5.3-.8.3Z" />
    </svg>
  );
}

/**
 * One result card. Structural difference between rental and sale stock, per
 * spec section 7: a rental row's facts are rent + deposit, a sale row's are
 * price + maintenance fee — that split changes the markup, not just a badge.
 *
 * Also the linked half of the search page's list <-> map hover: `onHover`
 * tells the map which pin to highlight, `active` reflects the map's own
 * hover/focus of this unit's pin back onto the row.
 */
export function UnitRow({
  unit,
  active = false,
  favourite = false,
  onHover,
}: {
  unit: UnitOut;
  active?: boolean;
  favourite?: boolean;
  onHover?: (id: number | null) => void;
}) {
  const [suosikki, setSuosikki] = useState(favourite);
  // Adjusted during render (not an effect) when the favourites list arrives
  // after this row already mounted — see
  // https://react.dev/learn/you-might-not-need-an-effect#adjusting-some-state-when-a-prop-changes
  const [lastFavouriteProp, setLastFavouriteProp] = useState(favourite);
  if (favourite !== lastFavouriteProp) {
    setLastFavouriteProp(favourite);
    setSuosikki(favourite);
  }
  const [pending, setPending] = useState(false);
  const isRental = unit.listing_type === "vuokra";
  const headlinePrice = isRental ? unit.rent_eur : unit.price_eur;

  async function toggleFavourite() {
    const next = !suosikki;
    setSuosikki(next);
    setPending(true);
    try {
      const sessionKey = getSessionKey();
      if (next) {
        await addFavourite(sessionKey, unit.id);
      } else {
        await removeFavourite(sessionKey, unit.id);
      }
    } catch {
      setSuosikki(!next); // the API call failed — don't leave the UI claiming a state that isn't saved
    } finally {
      setPending(false);
    }
  }

  return (
    <li
      className={`flex gap-4 rounded-lg border p-3 transition-colors sm:gap-5 sm:p-4 motion-reduce:transition-none ${
        active ? "border-accent bg-paper-raised" : "border-line bg-paper-raised"
      }`}
      onMouseEnter={() => onHover?.(unit.id)}
      onMouseLeave={() => onHover?.(null)}
    >
      <Link
        href={`/asunnot/${unit.id}`}
        onFocus={() => onHover?.(unit.id)}
        onBlur={() => onHover?.(null)}
        className="flex h-24 w-24 shrink-0 overflow-hidden rounded-md bg-[color-mix(in_srgb,var(--color-ink)_6%,var(--color-paper))] sm:h-32 sm:w-40"
      >
        {unit.primary_image ? (
          <Image
            src={unit.primary_image.url}
            alt={unit.primary_image.alt_fi}
            width={160}
            height={128}
            className="h-full w-full object-cover"
            unoptimized
          />
        ) : (
          <span className="flex h-full w-full items-center justify-center text-center text-xs text-ink-muted">
            {tekstit.kuvaPuuttuu}
          </span>
        )}
      </Link>

      <div className="flex min-w-0 flex-1 flex-col gap-1.5">
        <div className="flex items-start justify-between gap-3">
          <Link href={`/asunnot/${unit.id}`} className="tabular-nums text-2xl font-semibold leading-tight text-ink hover:underline">
            {headlinePrice !== null && headlinePrice !== undefined
              ? formatEuros(headlinePrice)
              : tekstit.eiTiedossa}
            {isRental && (
              <span className="ml-1 text-base font-normal text-ink-muted">
                / {tekstit.kuukausi}
              </span>
            )}
          </Link>
          <button
            type="button"
            disabled={pending}
            aria-pressed={suosikki}
            aria-label={suosikki ? tekstit.poistaSuosikeista : tekstit.lisaaSuosikkeihin}
            onClick={toggleFavourite}
            className="shrink-0 rounded-full p-1.5 text-ink-muted transition-colors hover:text-accent focus-visible:text-accent motion-reduce:transition-none"
          >
            <span className={suosikki ? "text-accent" : undefined}>
              <HeartIcon filled={suosikki} />
            </span>
          </button>
        </div>

        <Link href={`/asunnot/${unit.id}`} className="truncate text-sm text-ink-muted hover:underline">
          {unit.property_name} · {unit.street}, {unit.city}
        </Link>

        <p className="tabular-nums truncate text-sm text-ink">
          {unit.room_layout_fi} · {formatArea(unit.area_m2)} · {unit.floor}. krs
        </p>

        {isRental ? (
          <dl className="mt-1 grid grid-cols-2 gap-x-4 gap-y-0.5 text-sm">
            <div className="flex justify-between gap-2">
              <dt className="text-ink-muted">{tekstit.vuokra}</dt>
              <dd className="tabular-nums text-ink">
                {unit.rent_eur ? `${formatEuros(unit.rent_eur)} / ${tekstit.kuukausi}` : tekstit.eiTiedossa}
              </dd>
            </div>
            <div className="flex justify-between gap-2">
              <dt className="text-ink-muted">{tekstit.vakuus}</dt>
              <dd className="tabular-nums text-ink">
                {unit.deposit_eur ? formatEuros(unit.deposit_eur) : tekstit.eiTiedossa}
              </dd>
            </div>
          </dl>
        ) : (
          <dl className="mt-1 grid grid-cols-2 gap-x-4 gap-y-0.5 text-sm">
            <div className="flex justify-between gap-2">
              <dt className="text-ink-muted">{tekstit.velatonHinta}</dt>
              <dd className="tabular-nums text-ink">
                {unit.price_eur ? formatEuros(unit.price_eur) : tekstit.eiTiedossa}
              </dd>
            </div>
            <div className="flex justify-between gap-2">
              <dt className="text-ink-muted">{tekstit.hoitovastike}</dt>
              <dd className="tabular-nums text-ink">
                {unit.maintenance_fee_eur
                  ? `${formatEuros(unit.maintenance_fee_eur)} / ${tekstit.kuukausi}`
                  : tekstit.eiTiedossa}
              </dd>
            </div>
          </dl>
        )}
      </div>
    </li>
  );
}

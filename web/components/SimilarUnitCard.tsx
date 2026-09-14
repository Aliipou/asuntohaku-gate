import Image from "next/image";
import Link from "next/link";
import type { UnitOut } from "@/lib/api";
import { formatArea, formatEuros } from "@/lib/format";
import type { tekstit } from "@/lib/tekstit";

/** A compact card for screen 2's "Vastaavia asuntoja" (spec section 7). */
export function SimilarUnitCard({ unit, href, t }: { unit: UnitOut; href: string; t: typeof tekstit }) {
  const price = unit.listing_type === "vuokra" ? unit.rent_eur : unit.price_eur;
  return (
    <Link
      href={href}
      className="flex flex-col gap-1.5 rounded-lg border border-line bg-paper-raised p-3 hover:border-accent"
    >
      <div className="relative aspect-[4/3] w-full overflow-hidden rounded-md bg-[color-mix(in_srgb,var(--color-ink)_6%,var(--color-paper))]">
        {unit.primary_image ? (
          <Image
            src={unit.primary_image.url}
            alt={unit.primary_image.alt_fi}
            fill
            sizes="220px"
            className="object-cover"
            unoptimized
          />
        ) : (
          <span className="flex h-full w-full items-center justify-center text-center text-xs text-ink-muted">
            {t.kuvaPuuttuu}
          </span>
        )}
      </div>
      <p className="tabular-nums text-lg font-semibold text-ink">
        {price ? formatEuros(price) : t.eiTiedossa}
      </p>
      <p className="truncate text-sm text-ink-muted">
        {unit.property_name}, {unit.city}
      </p>
      <p className="tabular-nums text-sm text-ink">
        {unit.room_layout_fi} · {formatArea(unit.area_m2)}
      </p>
    </Link>
  );
}

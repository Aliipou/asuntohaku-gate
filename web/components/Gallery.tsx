"use client";

import { useState } from "react";
import Image from "next/image";
import type { UnitImageOut } from "@/lib/api";
import type { tekstit } from "@/lib/tekstit";

/**
 * Screen 2's image gallery (spec section 7): includes the floor plan
 * (`pohjapiirros`) as one of the image types, not a separate feature.
 */
export function Gallery({ images, t }: { images: UnitImageOut[]; t: typeof tekstit }) {
  const [index, setIndex] = useState(0);
  if (images.length === 0) return null;
  const current = images[index];

  function go(delta: number) {
    setIndex((i) => (i + delta + images.length) % images.length);
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="relative aspect-[4/3] w-full overflow-hidden rounded-lg bg-[color-mix(in_srgb,var(--color-ink)_6%,var(--color-paper))] sm:aspect-[16/9]">
        <Image
          src={current.url}
          alt={current.alt_fi}
          fill
          sizes="(min-width: 1024px) 66vw, 100vw"
          className="object-cover"
          unoptimized
          priority={index === 0}
        />
        {current.kind === "pohjapiirros" && (
          <span className="absolute left-3 top-3 rounded-full bg-paper-raised px-3 py-1 text-xs font-medium text-ink shadow-sm">
            {t.pohjapiirros}
          </span>
        )}
        {images.length > 1 && (
          <>
            <button
              type="button"
              onClick={() => go(-1)}
              aria-label={t.edellinenKuva}
              className="absolute left-2 top-1/2 -translate-y-1/2 rounded-full bg-paper-raised/90 p-2 text-ink shadow-sm hover:bg-paper-raised"
            >
              ‹
            </button>
            <button
              type="button"
              onClick={() => go(1)}
              aria-label={t.seuraavaKuva}
              className="absolute right-2 top-1/2 -translate-y-1/2 rounded-full bg-paper-raised/90 p-2 text-ink shadow-sm hover:bg-paper-raised"
            >
              ›
            </button>
            <span className="absolute bottom-2 right-2 rounded-full bg-ink/70 px-2 py-0.5 text-xs text-accent-ink tabular-nums">
              {t.kuvaNumero(index + 1, images.length)}
            </span>
          </>
        )}
      </div>

      <p className="text-xs text-ink-muted">{current.credit}</p>

      {images.length > 1 && (
        <div className="flex gap-2 overflow-x-auto pb-1">
          {images.map((image, i) => (
            <button
              key={image.url + i}
              type="button"
              onClick={() => setIndex(i)}
              aria-label={t.kuvaNumero(i + 1, images.length)}
              aria-current={i === index}
              className={`relative h-14 w-20 shrink-0 overflow-hidden rounded-md border ${
                i === index ? "border-accent" : "border-line"
              }`}
            >
              <Image src={image.url} alt="" fill sizes="80px" className="object-cover" unoptimized />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

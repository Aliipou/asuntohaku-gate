"use client";

import { useState } from "react";
import { ApiError, bookViewing, type ViewingOut } from "@/lib/api";
import { ensureApplicationToken } from "@/lib/browserState";
import { formatDate } from "@/lib/format";
import { pickTekstit, type Locale } from "@/lib/locale";

function formatTime(iso: string): string {
  const date = new Date(iso);
  return date.toLocaleTimeString("fi-FI", { hour: "2-digit", minute: "2-digit" });
}

/** Screen 2's "Varaa näyttöaika" (spec section 7, sale units). */
export function ViewingBooker({ viewings, locale }: { viewings: ViewingOut[]; locale: Locale }) {
  const t = pickTekstit(locale);
  const [selected, setSelected] = useState<number | null>(viewings[0]?.id ?? null);
  const [state, setState] = useState<"idle" | "pending" | "booked" | "error">("idle");
  const [message, setMessage] = useState<string | null>(null);

  if (viewings.length === 0) {
    return <p className="text-sm text-ink-muted">{t.eiNaytettavissa}</p>;
  }

  async function book() {
    if (selected === null) return;
    setState("pending");
    setMessage(null);
    try {
      const editToken = await ensureApplicationToken();
      await bookViewing(selected, { edit_token: editToken });
      setState("booked");
      setMessage(t.naytonVarausOnnistui);
    } catch (cause) {
      setState("error");
      setMessage(
        cause instanceof ApiError && cause.status === 409
          ? t.naytonVarausEpaonnistui
          : t.tarvitaanHakemusEnsin,
      );
    }
  }

  return (
    <div className="flex flex-col gap-2">
      <fieldset className="flex flex-col gap-1.5">
        <legend className="sr-only">{t.varaaNayttoaika}</legend>
        {viewings.map((viewing) => {
          const full = viewing.seats_left <= 0;
          return (
            <label
              key={viewing.id}
              className={`flex items-center justify-between gap-3 rounded-md border px-3 py-2 text-sm ${
                full ? "cursor-not-allowed border-line text-ink-muted" : "cursor-pointer border-line text-ink"
              } ${selected === viewing.id ? "border-accent" : ""}`}
            >
              <span className="flex items-center gap-2">
                <input
                  type="radio"
                  name="viewing"
                  value={viewing.id}
                  disabled={full}
                  checked={selected === viewing.id}
                  onChange={() => setSelected(viewing.id)}
                />
                {formatDate(viewing.starts_at)} klo {formatTime(viewing.starts_at)}
              </span>
              <span className="tabular-nums text-xs text-ink-muted">
                {full ? t.taynna : t.paikkojaJaljella(viewing.seats_left)}
              </span>
            </label>
          );
        })}
      </fieldset>

      <button
        type="button"
        onClick={book}
        disabled={selected === null || state === "pending" || state === "booked"}
        className="rounded-md border border-accent px-4 py-2 text-sm font-medium text-accent hover:bg-accent hover:text-accent-ink disabled:opacity-60"
      >
        {t.varaaValittuAika}
      </button>

      {message && (
        <p role="status" className="text-sm text-ink-muted">
          {message}
        </p>
      )}
    </div>
  );
}

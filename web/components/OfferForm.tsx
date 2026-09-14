"use client";

import { useState, type FormEvent } from "react";
import { ApiError, createOffer } from "@/lib/api";
import type { tekstit } from "@/lib/tekstit";

/** Screen 2's "Jätä tarjous" (spec section 7, sale units) — no application needed. */
export function OfferForm({ unitId, t }: { unitId: number; t: typeof tekstit }) {
  const [state, setState] = useState<"idle" | "pending" | "sent" | "error">("idle");
  const [message, setMessage] = useState<string | null>(null);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    setState("pending");
    setMessage(null);
    try {
      await createOffer(unitId, {
        contact_name: String(form.get("contact_name") ?? ""),
        contact_email: String(form.get("contact_email") ?? ""),
        amount_eur: String(form.get("amount_eur") ?? ""),
        message: String(form.get("message") ?? "") || null,
      });
      setState("sent");
      setMessage(t.tarjousLahetetty);
    } catch (cause) {
      setState("error");
      setMessage(cause instanceof ApiError ? cause.messageFi ?? t.tarjousEpaonnistui : t.tarjousEpaonnistui);
    }
  }

  if (state === "sent") {
    return (
      <p role="status" className="text-sm text-ink-muted">
        {message}
      </p>
    );
  }

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-2 text-sm">
      <label className="flex flex-col gap-1">
        <span className="font-medium text-ink">{t.tarjoajanNimi}</span>
        <input
          name="contact_name"
          type="text"
          required
          maxLength={160}
          className="rounded-md border border-line bg-paper-raised px-2 py-1.5 text-ink outline-none focus-visible:border-accent"
        />
      </label>
      <label className="flex flex-col gap-1">
        <span className="font-medium text-ink">{t.sahkoposti}</span>
        <input
          name="contact_email"
          type="email"
          required
          maxLength={254}
          className="rounded-md border border-line bg-paper-raised px-2 py-1.5 text-ink outline-none focus-visible:border-accent"
        />
      </label>
      <label className="flex flex-col gap-1">
        <span className="font-medium text-ink">{t.tarjousSumma}</span>
        <input
          name="amount_eur"
          type="number"
          inputMode="numeric"
          min={1}
          step="1"
          required
          className="rounded-md border border-line bg-paper-raised px-2 py-1.5 text-ink outline-none focus-visible:border-accent"
        />
      </label>
      <label className="flex flex-col gap-1">
        <span className="font-medium text-ink">{t.viestiValinnainen}</span>
        <textarea
          name="message"
          rows={2}
          className="rounded-md border border-line bg-paper-raised px-2 py-1.5 text-ink outline-none focus-visible:border-accent"
        />
      </label>

      <button
        type="submit"
        disabled={state === "pending"}
        className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-accent-ink hover:opacity-90 disabled:opacity-60"
      >
        {t.lahetaTarjousPainike}
      </button>

      {state === "error" && message && (
        <p role="alert" className="text-ink-muted">
          {message}
        </p>
      )}
    </form>
  );
}

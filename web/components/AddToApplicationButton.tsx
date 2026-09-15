"use client";

import { useState } from "react";
import Link from "next/link";
import { addApplicationUnit, ApiError } from "@/lib/api";
import { ensureApplicationToken } from "@/lib/browserState";
import { pickTekstit, type Locale } from "@/lib/locale";

/**
 * Screen 2's primary action for rental stock (spec section 7). Starts an
 * application on first use if the visitor doesn't have one yet — see
 * lib/browserState.ts's ensureApplicationToken — then adds this unit to its
 * basket. api/app/routers/applications.py already refuses a unit already in
 * the basket (409) and any non-rental unit (400); both surface as a plain
 * message rather than a crash.
 */
export function AddToApplicationButton({
  unitId,
  langSuffix,
  locale,
}: {
  unitId: number;
  langSuffix: string;
  locale: Locale;
}) {
  const t = pickTekstit(locale);
  const [state, setState] = useState<"idle" | "pending" | "added" | "error">("idle");
  const [token, setToken] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function add() {
    setState("pending");
    setErrorMessage(null);
    try {
      const editToken = await ensureApplicationToken();
      await addApplicationUnit(editToken, { unit_id: unitId });
      setToken(editToken);
      setState("added");
    } catch (cause) {
      // Already in the basket is not a failure worth alarming over — it just
      // means the visitor's application already has this unit.
      if (cause instanceof ApiError && cause.status === 409) {
        setToken(await ensureApplicationToken().catch(() => null));
        setState("added");
        return;
      }
      setErrorMessage(cause instanceof ApiError ? cause.messageFi ?? cause.message : String(cause));
      setState("error");
    }
  }

  if (state === "added" && token) {
    return (
      <Link
        href={`/hakemus/${token}${langSuffix}`}
        className="block rounded-md bg-accent px-4 py-2.5 text-center text-sm font-medium text-accent-ink hover:opacity-90"
      >
        {t.avaaHakemus}
      </Link>
    );
  }

  return (
    <div className="flex flex-col gap-1.5">
      <button
        type="button"
        onClick={add}
        disabled={state === "pending"}
        className="rounded-md bg-accent px-4 py-2.5 text-sm font-medium text-accent-ink hover:opacity-90 disabled:opacity-60"
      >
        {t.lisaaHakemukseen}
      </button>
      {state === "error" && errorMessage && (
        <p role="alert" className="text-sm text-ink-muted">
          {errorMessage}
        </p>
      )}
    </div>
  );
}

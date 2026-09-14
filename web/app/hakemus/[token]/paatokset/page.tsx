import { notFound } from "next/navigation";
import Link from "next/link";
import { ApiError, getDecisions } from "@/lib/api";
import { sovellusTekstit as t } from "@/lib/tekstitSovellus";
import { DecisionRow } from "@/components/DecisionRow";

export const dynamic = "force-dynamic";

interface PaatoksetPageProps {
  params: Promise<{ token: string }>;
}

/**
 * Päätökset — one row per chosen apartment, its outcome, the plain Finnish
 * reason, and the value that decided it (spec section 7, screen 4 — "this
 * screen is the product; give it the most design attention"). Decisions are
 * rendered exactly as the API returns them: this page computes nothing.
 */
export default async function PaatoksetPage({ params }: PaatoksetPageProps) {
  const { token } = await params;

  let decisions;
  try {
    decisions = await getDecisions(token);
  } catch (cause) {
    if (cause instanceof ApiError && cause.status === 404) {
      notFound();
    }
    return (
      <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-6 sm:px-6">
        <p role="alert" className="rounded-md border border-line bg-paper-raised p-4 text-ink">
          {t.hakemuksenLataaminenEpaonnistui}
        </p>
      </main>
    );
  }

  return (
    <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-6 sm:px-6">
      <div className="mb-4 flex items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold text-ink">{t.paatoksetOtsikko}</h1>
        <Link href={`/hakemus/${token}`} className="text-sm text-accent hover:underline">
          {t.takaisinHakemukseen}
        </Link>
      </div>

      {decisions.length === 0 ? (
        <p className="text-sm text-ink-muted">{t.eiPaatoksia}</p>
      ) : (
        <ul className="flex flex-col gap-4">
          {decisions.map((decision) => (
            <DecisionRow key={decision.unit_id} decision={decision} token={token} />
          ))}
        </ul>
      )}
    </main>
  );
}

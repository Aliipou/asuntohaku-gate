import { notFound } from "next/navigation";
import Link from "next/link";
import { ApiError, getDecisions } from "@/lib/api";
import { fieldIdForEvidence } from "@/lib/decisionFieldLinks";
import { sovellusTekstit as t } from "@/lib/tekstitSovellus";
import { OutcomeBadge } from "@/components/OutcomeBadge";

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
          {decisions.map((decision) => {
            const fieldId = decision.outcome === "puuttuvat_tiedot" ? fieldIdForEvidence(decision.evidence) : null;
            return (
              <li key={decision.unit_id} className="rounded-lg border border-line bg-paper-raised p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <h2 className="font-medium text-ink">{decision.unit_label}</h2>
                  <OutcomeBadge outcome={decision.outcome} label={decision.outcome_label_fi} />
                </div>

                <p className="mt-2 text-ink">{decision.message_fi}</p>

                {decision.evidence.length > 0 && (
                  <div className="mt-3">
                    <p className="text-xs font-medium uppercase tracking-wide text-ink-muted">
                      {t.ratkaisevatTiedot}
                    </p>
                    <ul className="mt-1 flex flex-col gap-0.5 text-sm text-ink">
                      {decision.evidence.map((item) => (
                        <li key={item.avain}>{item.teksti}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {fieldId && (
                  <Link
                    href={`/hakemus/${token}#${fieldId}`}
                    className="mt-3 inline-block text-sm font-medium text-accent hover:underline"
                  >
                    {t.taydennaHakemuksessa}
                  </Link>
                )}

                {decision.rules.length > 1 && (
                  <details className="mt-3 text-sm">
                    <summary className="cursor-pointer text-ink-muted">{t.peruste}</summary>
                    <ul className="mt-2 flex flex-col gap-2">
                      {decision.rules.map((rule) => (
                        <li key={rule.rule_id} className="flex items-start justify-between gap-3">
                          <span className="text-ink-muted">{rule.rule_title_fi}</span>
                          <OutcomeBadge outcome={rule.outcome} label={rule.outcome_label_fi} />
                        </li>
                      ))}
                    </ul>
                  </details>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </main>
  );
}

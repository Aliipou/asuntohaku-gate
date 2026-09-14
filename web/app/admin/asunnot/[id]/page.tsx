import { notFound } from "next/navigation";
import { ApiError, getRankedApplicants } from "@/lib/api";
import { ASUMISMUOTO_LABELS } from "@/lib/tekstit";
import { OUTCOME_LABELS_FI, sovellusTekstit as t } from "@/lib/tekstitSovellus";
import { OutcomeBadge } from "@/components/OutcomeBadge";

export const dynamic = "force-dynamic";

interface AdminUnitPageProps {
  params: Promise<{ id: string }>;
}

/**
 * Asukasvalinta — for one apartment, the ranked applicants and the basis for
 * the order (spec section 7, screen 5). Unauthenticated, unlinked from the
 * rest of the app, exactly as api/app/routers/admin.py's own docstring says.
 */
export default async function AdminUnitPage({ params }: AdminUnitPageProps) {
  const { id } = await params;
  const unitId = Number(id);
  if (!Number.isInteger(unitId)) {
    notFound();
  }

  let ranking;
  try {
    ranking = await getRankedApplicants(unitId);
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
      <h1 className="text-2xl font-semibold text-ink">{t.asukasvalintaOtsikko}</h1>
      <p className="mt-1 text-ink-muted">
        {ranking.unit_label} — {ASUMISMUOTO_LABELS[ranking.housing_form]}
      </p>

      <p className="mt-4 rounded-md border border-line bg-paper-raised p-3 text-sm text-ink">
        {ranking.ranking_basis_fi ?? t.eiJarjestyssaantoa}
      </p>

      {ranking.applicants.length === 0 ? (
        <p className="mt-4 text-sm text-ink-muted">{t.eiHakijoita}</p>
      ) : (
        <ol className="mt-4 flex flex-col gap-3">
          {ranking.applicants.map((applicant) => (
            <li key={applicant.application_id} className="rounded-lg border border-line bg-paper-raised p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <p className="font-medium text-ink">
                  <span className="tabular-nums text-ink-muted">
                    {t.sija} {applicant.rank}
                  </span>{" "}
                  · {applicant.contact_name ?? t.hakijaNimeton}
                </p>
                <OutcomeBadge outcome={applicant.eligibility} label={OUTCOME_LABELS_FI[applicant.eligibility]} />
              </div>

              <p className="mt-2 text-sm text-ink-muted">{applicant.eligibility_message_fi}</p>

              <p className="mt-3 text-sm text-ink">{applicant.message_fi}</p>

              {applicant.evidence.length > 0 && (
                <ul className="mt-2 flex flex-col gap-0.5 text-sm text-ink-muted">
                  {applicant.evidence.map((item) => (
                    <li key={item.avain}>{item.teksti}</li>
                  ))}
                </ul>
              )}
            </li>
          ))}
        </ol>
      )}
    </main>
  );
}

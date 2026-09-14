import Link from "next/link";
import type { DecisionOut } from "@/lib/api";
import { fieldIdForEvidence } from "@/lib/decisionFieldLinks";
import { sovellusTekstit as t } from "@/lib/tekstitSovellus";
import { OutcomeBadge } from "./OutcomeBadge";

/**
 * One row of the Päätökset screen (spec section 7, screen 4): rendered
 * exactly as the API returns it — rule id (via OutcomeBadge/details), the
 * Finnish message and the evidence that decided it. A `puuttuvat_tiedot` row
 * links back to the exact Hakemus field. Pulled out of the page itself so it
 * can be unit-tested without rendering an async server component.
 */
export function DecisionRow({ decision, token }: { decision: DecisionOut; token: string }) {
  const fieldId = decision.outcome === "puuttuvat_tiedot" ? fieldIdForEvidence(decision.evidence) : null;

  return (
    <li className="rounded-lg border border-line bg-paper-raised p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <h2 className="font-medium text-ink">{decision.unit_label}</h2>
        <OutcomeBadge outcome={decision.outcome} label={decision.outcome_label_fi} />
      </div>

      <p className="mt-2 text-ink">{decision.message_fi}</p>

      {decision.evidence.length > 0 && (
        <div className="mt-3">
          <p className="text-xs font-medium uppercase tracking-wide text-ink-muted">{t.ratkaisevatTiedot}</p>
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
}

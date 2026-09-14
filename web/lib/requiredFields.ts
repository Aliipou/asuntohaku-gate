/**
 * Which of the fields GET /applications/{token}/required-fields lists are
 * still unfilled on this application, so the Hakemus screen can say what is
 * missing rather than show a percentage (spec section 7, screen 3).
 *
 * This is a client-side read of already-fetched state, not a decision: the
 * only source of truth for whether an application is actually eligible is
 * GET /applications/{token}/decisions (see lib/tekstit.ts "do not compute...
 * an outcome" — this module never produces one, it only drives which form
 * section is open).
 */

import type { ApplicationOut, RequiredFieldOut } from "./api";

const FIELD_IS_MISSING: Record<string, (application: ApplicationOut) => boolean> = {
  household_income: (a) => !a.members.some((m) => m.gross_monthly_income_eur != null),
  assets: (a) => !a.members.some((m) => m.assets_eur != null),
  household_size: (a) => a.members.length === 0,
  housing_need: (a) => a.housing_need === null,
  order_number: (a) => !a.order_number,
  deposit_acknowledged: (a) => a.deposit_acknowledged !== true,
  credit_record: (a) => a.credit_default_flag === null || a.credit_default_flag === undefined,
};

export function isFieldMissing(field: string, application: ApplicationOut): boolean {
  return FIELD_IS_MISSING[field]?.(application) ?? true;
}

export function missingFields(
  required: RequiredFieldOut[],
  application: ApplicationOut,
): RequiredFieldOut[] {
  return required.filter((f) => isFieldMissing(f.field, application));
}

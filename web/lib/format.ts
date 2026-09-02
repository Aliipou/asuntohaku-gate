/**
 * Finnish display formatting for numbers, currency and dates.
 *
 * Deliberately hand-rolled rather than `Intl.NumberFormat('fi-FI', ...)`:
 * the ICU grouping separator for fi-FI has changed between platform versions
 * (some emit U+00A0 NO-BREAK SPACE, newer CLDR data emits U+202F NARROW
 * NO-BREAK SPACE), and the spec fixes the character at U+00A0. Formatting by
 * hand keeps the exact character stable regardless of the Node/ICU build the
 * app runs on.
 */

/** U+00A0 NO-BREAK SPACE — used as the thousands separator and before "€". */
const NBSP = " ";

function toNumber(value: string | number): number {
  const n = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(n)) {
    throw new RangeError(`Ei voitu tulkita numeroksi: ${JSON.stringify(value)}`);
  }
  return n;
}

/** Groups a plain-digit string into thousands, joined with NBSP: "1234567" -> "1 234 567". */
function groupThousands(digits: string): string {
  const reversedGroups: string[] = [];
  for (let end = digits.length; end > 0; end -= 3) {
    reversedGroups.push(digits.slice(Math.max(0, end - 3), end));
  }
  return reversedGroups.reverse().join(NBSP);
}

/**
 * Formats a euro amount the Finnish way: two decimals, comma as the decimal
 * separator, a non-breaking space between thousand groups, and a
 * non-breaking space before the euro sign — e.g. "1 234,50 €".
 *
 * Accepts the string the API sends (a serialised `Decimal`, e.g. "895.00")
 * or a plain number.
 */
export function formatEuros(value: string | number): string {
  const n = toNumber(value);
  const sign = n < 0 ? "-" : "";
  const [intDigits, fractionDigits] = Math.abs(n).toFixed(2).split(".");
  return `${sign}${groupThousands(intDigits)},${fractionDigits}${NBSP}€`;
}

/**
 * Formats a floor area the Finnish way: comma decimal, one decimal place,
 * trimmed when it is a whole number — e.g. "54,5 m²", "30 m²".
 */
export function formatArea(value: string | number): string {
  const n = toNumber(value);
  const rounded = Math.round(n * 10) / 10;
  const text = Number.isInteger(rounded) ? String(rounded) : rounded.toFixed(1).replace(".", ",");
  return `${text} m²`;
}

/**
 * Formats a date as d.m.yyyy (no zero-padding), the Finnish convention.
 * Accepts an ISO date/date-time string or a Date. Bare "YYYY-MM-DD" strings
 * are parsed as local midnight, not UTC, so the calendar day never shifts
 * depending on the reader's time zone.
 */
export function formatDate(value: string | Date): string {
  let date: Date;
  if (typeof value === "string") {
    date = /^\d{4}-\d{2}-\d{2}$/.test(value) ? new Date(`${value}T00:00:00`) : new Date(value);
  } else {
    date = value;
  }
  if (Number.isNaN(date.getTime())) {
    throw new RangeError(`Ei voitu tulkita päivämääräksi: ${JSON.stringify(value)}`);
  }
  return `${date.getDate()}.${date.getMonth() + 1}.${date.getFullYear()}`;
}

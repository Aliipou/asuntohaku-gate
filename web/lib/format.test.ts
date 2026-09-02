import { describe, expect, it } from "vitest";
import { formatArea, formatDate, formatEuros } from "./format";

describe("formatEuros", () => {
  it("uses a comma decimal separator and a non-breaking space before the euro sign", () => {
    const result = formatEuros("895.00");
    expect(result).toBe("895,00 €");
  });

  it("groups thousands with a non-breaking space, not a comma or a plain space", () => {
    const result = formatEuros(1234.5);
    expect(result).toBe("1 234,50 €");
    expect(result).not.toContain("1,234");
    // No plain ASCII space anywhere — every separator must be U+00A0.
    expect(result.includes(" ")).toBe(false);
  });

  it("handles amounts with multiple thousand groups", () => {
    expect(formatEuros("1234567.9")).toBe("1 234 567,90 €");
  });

  it("parses the Decimal-as-string values the API sends without float rounding surprises", () => {
    // 895.10 cannot be represented exactly as a binary float; a naive
    // toFixed(2) after a bad round-trip could yield "895,09" or "895,11".
    expect(formatEuros("895.10")).toBe("895,10 €");
  });

  it("keeps a minus sign in front of a negative amount", () => {
    expect(formatEuros(-42)).toBe("-42,00 €");
  });

  it("rejects a value that cannot be interpreted as a number", () => {
    expect(() => formatEuros("ei numero")).toThrow(RangeError);
  });
});

describe("formatArea", () => {
  it("formats with a Finnish decimal comma and trims a redundant trailing zero", () => {
    expect(formatArea("54.50")).toBe("54,5 m²");
  });

  it("keeps a genuine single decimal", () => {
    expect(formatArea("72.30")).toBe("72,3 m²");
  });

  it("renders a whole number of square metres with no decimal point at all", () => {
    expect(formatArea("30.00")).toBe("30 m²");
  });
});

describe("formatDate", () => {
  it("formats an ISO date as d.m.yyyy with no zero-padding", () => {
    expect(formatDate("2026-09-02")).toBe("2.9.2026");
    expect(formatDate("2026-01-05")).toBe("5.1.2026");
  });

  it("parses a bare date as local midnight so the day never shifts across time zones", () => {
    // A naive `new Date("2026-01-01")` parses as UTC midnight, which reads
    // back as 31.12.2025 in any negative-UTC-offset zone. Guard against that
    // regression explicitly.
    expect(formatDate("2026-01-01")).toBe("1.1.2026");
  });

  it("rejects an unparsable date", () => {
    expect(() => formatDate("not-a-date")).toThrow(RangeError);
  });
});

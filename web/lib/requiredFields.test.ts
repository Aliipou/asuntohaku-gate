import { describe, expect, it } from "vitest";
import { isFieldMissing, missingFields } from "./requiredFields";
import type { ApplicationOut, RequiredFieldOut } from "./api";

function application(overrides: Partial<ApplicationOut> = {}): ApplicationOut {
  return {
    edit_token: "t",
    status: "luonnos",
    created_at: "2026-01-01T00:00:00Z",
    expires_at: "2026-04-01T00:00:00Z",
    expired: false,
    contact_name: null,
    contact_email: null,
    contact_phone: null,
    order_number: null,
    deposit_acknowledged: null,
    credit_default_flag: null,
    members: [],
    housing_need: null,
    units: [],
    ...overrides,
  };
}

function requiredField(field: string): RequiredFieldOut {
  return { field, label_fi: field, required_by: [{ unit_id: 1, unit_label: "A", rule_id: "R", rule_title_fi: "R" }] };
}

describe("isFieldMissing", () => {
  it("treats household_income as missing until some member has an income", () => {
    expect(isFieldMissing("household_income", application())).toBe(true);
    expect(
      isFieldMissing(
        "household_income",
        application({ members: [{ id: 1, role: "paahakija", gross_monthly_income_eur: "2500.00" }] }),
      ),
    ).toBe(false);
  });

  it("treats deposit_acknowledged as missing unless it is exactly true", () => {
    expect(isFieldMissing("deposit_acknowledged", application({ deposit_acknowledged: false }))).toBe(true);
    expect(isFieldMissing("deposit_acknowledged", application({ deposit_acknowledged: true }))).toBe(false);
  });

  it("treats credit_record as missing until it has been answered either way", () => {
    expect(isFieldMissing("credit_record", application({ credit_default_flag: null }))).toBe(true);
    expect(isFieldMissing("credit_record", application({ credit_default_flag: false }))).toBe(false);
    expect(isFieldMissing("credit_record", application({ credit_default_flag: true }))).toBe(false);
  });

  it("treats housing_need as missing until it is set", () => {
    expect(isFieldMissing("housing_need", application())).toBe(true);
    expect(
      isFieldMissing("housing_need", application({ housing_need: { situation: "ahtaasti" } })),
    ).toBe(false);
  });

  it("treats an unrecognised field as missing rather than silently passing", () => {
    expect(isFieldMissing("something_unknown", application())).toBe(true);
  });
});

describe("missingFields", () => {
  it("filters the required-fields list down to only what is actually unfilled", () => {
    const required = [requiredField("household_income"), requiredField("deposit_acknowledged")];
    const app = application({ deposit_acknowledged: true });
    expect(missingFields(required, app).map((f) => f.field)).toEqual(["household_income"]);
  });

  it("returns nothing missing once every required field is filled", () => {
    const required = [requiredField("order_number")];
    const app = application({ order_number: "AO-123" });
    expect(missingFields(required, app)).toEqual([]);
  });
});

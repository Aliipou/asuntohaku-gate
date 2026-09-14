import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { HakemusForm } from "./HakemusForm";
import type { ApplicationOut, RequiredFieldOut } from "@/lib/api";

/**
 * AnimatedSection keeps a closed section's content mounted (so it can
 * collapse rather than vanish — see components/AnimatedSection.tsx) and
 * marks the wrapper `aria-hidden`/`inert` instead. So "does this section
 * show" is this attribute, not DOM presence of its heading text.
 */
function isSectionOpen(headingText: string): boolean {
  const heading = screen.getByText(headingText);
  const wrapper = heading.closest("[aria-hidden]");
  return wrapper?.getAttribute("aria-hidden") === "false";
}

function application(overrides: Partial<ApplicationOut> = {}): ApplicationOut {
  return {
    edit_token: "tok",
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
    units: [{ unit_id: 1, unit_label: "Kalliolan portti A 12", housing_form: "vapaarahoitteinen", preference_rank: 1 }],
    ...overrides,
  };
}

function requiredField(field: string): RequiredFieldOut {
  return {
    field,
    label_fi: field,
    required_by: [{ unit_id: 1, unit_label: "Kalliolan portti A 12", rule_id: "R", rule_title_fi: "Sääntö" }],
  };
}

describe("HakemusForm — adaptive sections", () => {
  it("shows no optional section when nothing is required yet", () => {
    render(<HakemusForm token="tok" initialApplication={application()} initialRequired={[]} />);
    expect(isSectionOpen("Ruokakunta")).toBe(false);
    expect(isSectionOpen("Asunnon tarve")).toBe(false);
    expect(isSectionOpen("Vakuus")).toBe(false);
  });

  it("shows the household section, and which apartment caused it, once household_income is required", () => {
    render(
      <HakemusForm
        token="tok"
        initialApplication={application()}
        initialRequired={[requiredField("household_income")]}
      />,
    );
    expect(isSectionOpen("Ruokakunta")).toBe(true);
    expect(screen.getByText("Kalliolan portti A 12 vaatii tämän (Sääntö)")).toBeInTheDocument();
    // A field the basket doesn't require yet still doesn't show.
    expect(isSectionOpen("Asunnon tarve")).toBe(false);
  });

  it("shows the deposit and credit-record sections independently", () => {
    render(
      <HakemusForm
        token="tok"
        initialApplication={application()}
        initialRequired={[requiredField("deposit_acknowledged"), requiredField("credit_record")]}
      />,
    );
    expect(isSectionOpen("Vakuus")).toBe(true);
    expect(isSectionOpen("Luottotiedot")).toBe(true);
    expect(isSectionOpen("Ruokakunta")).toBe(false);
  });

  it("states what is still missing as prose, not a percentage", () => {
    render(
      <HakemusForm
        token="tok"
        initialApplication={application()}
        initialRequired={[requiredField("order_number")]}
      />,
    );
    expect(screen.getByText("Vielä puuttuu:")).toBeInTheDocument();
    expect(screen.queryByText(/%/)).not.toBeInTheDocument();
  });

  it("has nothing missing once every required field is already filled on the application", () => {
    render(
      <HakemusForm
        token="tok"
        initialApplication={application({ deposit_acknowledged: true })}
        initialRequired={[requiredField("deposit_acknowledged")]}
      />,
    );
    expect(screen.queryByText("Vielä puuttuu:")).not.toBeInTheDocument();
  });
});

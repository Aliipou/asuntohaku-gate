import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { DecisionRow } from "./DecisionRow";
import type { DecisionOut } from "@/lib/api";

function decision(overrides: Partial<DecisionOut>): DecisionOut {
  return {
    unit_id: 1,
    unit_label: "Kalliolan portti A 12",
    housing_form: "vapaarahoitteinen",
    outcome: "kelpoinen",
    outcome_label_fi: "Kelpoinen",
    deciding_rule_id: "R-1",
    message_fi: "Hakemus täyttää ehdot.",
    evidence: [{ avain: "tulot", arvo: "2500.00", teksti: "Ruokakunnan tulot: 2 500,00 €" }],
    rules: [],
    ...overrides,
  };
}

describe("DecisionRow", () => {
  it("renders a kelpoinen decision with its outcome label, message and evidence", () => {
    render(<DecisionRow decision={decision({})} token="tok" />);
    expect(screen.getByText("Kelpoinen")).toBeInTheDocument();
    expect(screen.getByText("Hakemus täyttää ehdot.")).toBeInTheDocument();
    expect(screen.getByText("Ruokakunnan tulot: 2 500,00 €")).toBeInTheDocument();
  });

  it("renders an ei_kelpoinen decision the same way, with no link back to the form", () => {
    render(
      <DecisionRow
        decision={decision({
          outcome: "ei_kelpoinen",
          outcome_label_fi: "Ei kelpoinen",
          message_fi: "Ruokakunnan koko ei sovi asunnon huoneiden määrään.",
        })}
        token="tok"
      />,
    );
    expect(screen.getByText("Ei kelpoinen")).toBeInTheDocument();
    expect(screen.getByText("Ruokakunnan koko ei sovi asunnon huoneiden määrään.")).toBeInTheDocument();
    expect(screen.queryByRole("link")).not.toBeInTheDocument();
  });

  it("renders a puuttuvat_tiedot decision with a link back to the exact Hakemus field", () => {
    render(
      <DecisionRow
        decision={decision({
          outcome: "puuttuvat_tiedot",
          outcome_label_fi: "Puuttuvat tiedot",
          message_fi: "Ruokakunnan tulot puuttuvat.",
          evidence: [{ avain: "puuttuva_tieto", arvo: "ruokakunnan_bruttotulot", teksti: "Puuttuu: ruokakunnan tulot" }],
        })}
        token="tok"
      />,
    );
    expect(screen.getByText("Puuttuvat tiedot")).toBeInTheDocument();
    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("href", "/hakemus/tok#household_income");
  });

  it("does not add a field link when the missing-info vocabulary names no known field", () => {
    render(
      <DecisionRow
        decision={decision({
          outcome: "puuttuvat_tiedot",
          outcome_label_fi: "Puuttuvat tiedot",
          evidence: [{ avain: "puuttuva_tieto", arvo: "tietojen_vahvistus", teksti: "Vahvista tiedot" }],
        })}
        token="tok"
      />,
    );
    expect(screen.queryByRole("link")).not.toBeInTheDocument();
  });

  it("shows every rule outcome behind a disclosure when more than one rule was evaluated", () => {
    render(
      <DecisionRow
        decision={decision({
          rules: [
            {
              rule_id: "R-1",
              rule_title_fi: "Tulorajasääntö",
              outcome: "kelpoinen",
              outcome_label_fi: "Kelpoinen",
              message_fi: "Tulot alittavat rajan.",
              evidence: [],
            },
            {
              rule_id: "R-2",
              rule_title_fi: "Ruokakunnan kokosääntö",
              outcome: "kelpoinen",
              outcome_label_fi: "Kelpoinen",
              message_fi: "Koko sopii asuntoon.",
              evidence: [],
            },
          ],
        })}
        token="tok"
      />,
    );
    expect(screen.getByText("Tulorajasääntö")).toBeInTheDocument();
    expect(screen.getByText("Ruokakunnan kokosääntö")).toBeInTheDocument();
  });
});

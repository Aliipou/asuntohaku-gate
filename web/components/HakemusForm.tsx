"use client";

import { useState } from "react";
import Link from "next/link";
import {
  ApiError,
  getRequiredFields,
  removeApplicationUnit,
  updateApplication,
  type ApplicationOut,
  type MemberIn,
  type NeedSituation,
  type RequiredFieldOut,
} from "@/lib/api";
import { missingFields } from "@/lib/requiredFields";
import {
  MEMBER_ROLE_LABELS,
  NEED_SITUATION_LABELS,
  sovellusTekstit as t,
} from "@/lib/tekstitSovellus";
import { AnimatedSection } from "./AnimatedSection";

type EditableMember = MemberIn & { key: string };

function toEditableMembers(members: ApplicationOut["members"]): EditableMember[] {
  return members.map((m) => ({ ...m, key: String(m.id) }));
}

function memberWithoutKey(member: EditableMember): MemberIn {
  const { role, birth_year, gross_monthly_income_eur, assets_eur } = member;
  return { role, birth_year, gross_monthly_income_eur, assets_eur };
}

/** Causes for one required field, as "Unit label vaatii tämän (Rule title)" lines. */
function Causes({ field }: { field: RequiredFieldOut }) {
  return (
    <ul className="mt-1 flex flex-col gap-0.5 text-sm text-ink-muted">
      {field.required_by.map((cause) => (
        <li key={`${cause.unit_id}-${cause.rule_id}`}>
          {t.vaatiiAsunnon(cause.unit_label, cause.rule_title_fi)}
        </li>
      ))}
    </ul>
  );
}

export function HakemusForm({
  token,
  initialApplication,
  initialRequired,
}: {
  token: string;
  initialApplication: ApplicationOut;
  initialRequired: RequiredFieldOut[];
}) {
  const [application, setApplication] = useState(initialApplication);
  const [required, setRequired] = useState(initialRequired);

  const [contactName, setContactName] = useState(application.contact_name ?? "");
  const [contactEmail, setContactEmail] = useState(application.contact_email ?? "");
  const [contactPhone, setContactPhone] = useState(application.contact_phone ?? "");
  const [orderNumber, setOrderNumber] = useState(application.order_number ?? "");
  const [depositAcknowledged, setDepositAcknowledged] = useState(
    application.deposit_acknowledged ?? false,
  );
  const [creditDefaultFlag, setCreditDefaultFlag] = useState<boolean | null>(
    application.credit_default_flag ?? null,
  );
  const [members, setMembers] = useState<EditableMember[]>(toEditableMembers(application.members));
  const [needSituation, setNeedSituation] = useState<NeedSituation | "">(
    application.housing_need?.situation ?? "",
  );
  const [needNote, setNeedNote] = useState(application.housing_need?.urgency_note ?? "");

  const [saveState, setSaveState] = useState<"idle" | "pending" | "saved" | "error">("idle");
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  const has = (field: string) => required.some((f) => f.field === field);
  const missing = missingFields(required, application);

  function addMember() {
    setMembers((prev) => [
      ...prev,
      { key: `new-${prev.length}-${Date.now()}`, role: "muu", birth_year: null, gross_monthly_income_eur: null, assets_eur: null },
    ]);
  }

  function removeMember(key: string) {
    setMembers((prev) => prev.filter((m) => m.key !== key));
  }

  function updateMember(key: string, patch: Partial<EditableMember>) {
    setMembers((prev) => prev.map((m) => (m.key === key ? { ...m, ...patch } : m)));
  }

  async function refreshRequired() {
    try {
      setRequired(await getRequiredFields(token));
    } catch {
      // Keep the last known list rather than blanking the form on a hiccup.
    }
  }

  async function onRemoveUnit(unitId: number) {
    try {
      const updated = await removeApplicationUnit(token, unitId);
      setApplication(updated);
      await refreshRequired();
    } catch {
      // The unit stays in the basket; nothing to reconcile locally.
    }
  }

  async function onSave() {
    setSaveState("pending");
    setSaveMessage(null);
    try {
      const updated = await updateApplication(token, {
        contact_name: contactName || null,
        contact_email: contactEmail || null,
        contact_phone: contactPhone || null,
        order_number: has("order_number") ? orderNumber || null : undefined,
        deposit_acknowledged: has("deposit_acknowledged") ? depositAcknowledged : undefined,
        credit_default_flag: has("credit_record") ? creditDefaultFlag : undefined,
        members:
          has("household_income") || has("assets") || has("household_size")
            ? members.map(memberWithoutKey)
            : undefined,
        housing_need: has("housing_need") && needSituation ? { situation: needSituation, urgency_note: needNote || null } : undefined,
      });
      setApplication(updated);
      await refreshRequired();
      setSaveState("saved");
      setSaveMessage(t.tallennettu);
    } catch (cause) {
      setSaveState("error");
      setSaveMessage(cause instanceof ApiError ? cause.messageFi ?? t.tallennusEpaonnistui : t.tallennusEpaonnistui);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <section>
        <h2 className="mb-2 text-lg font-semibold text-ink">{t.ostoskori}</h2>
        {application.units.length === 0 ? (
          <p className="text-sm text-ink-muted">{t.koriOnTyhja}</p>
        ) : (
          <ul className="flex flex-col gap-2">
            {application.units.map((au) => (
              <li
                key={au.unit_id}
                className="flex items-center justify-between gap-3 rounded-md border border-line bg-paper-raised px-3 py-2 text-sm"
              >
                <span>{au.unit_label}</span>
                <button
                  type="button"
                  onClick={() => onRemoveUnit(au.unit_id)}
                  className="text-accent hover:underline"
                >
                  {t.poistaKorista}
                </button>
              </li>
            ))}
          </ul>
        )}
        <div className="mt-2 flex gap-4 text-sm">
          <Link href="/" className="text-accent hover:underline">
            {t.etsiAsuntoja}
          </Link>
          {application.units.length > 0 && (
            <Link href={`/hakemus/${token}/paatokset`} className="text-accent hover:underline">
              {t.katsoPaatokset}
            </Link>
          )}
        </div>
      </section>

      {missing.length > 0 && (
        <section className="rounded-md border border-line bg-paper-raised p-3">
          <p className="font-medium text-ink">{t.puuttuuViela}</p>
          <ul className="mt-1 flex flex-col gap-2">
            {missing.map((field) => (
              <li key={field.field}>
                <p className="text-sm text-ink">{field.label_fi}</p>
                <Causes field={field} />
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="flex flex-col gap-2">
        <h2 className="text-lg font-semibold text-ink">{t.yhteystiedot}</h2>
        <label className="flex flex-col gap-1 text-sm">
          <span className="font-medium text-ink">{t.nimi}</span>
          <input
            value={contactName}
            onChange={(e) => setContactName(e.target.value)}
            className="rounded-md border border-line bg-paper-raised px-2 py-1.5 text-ink outline-none focus-visible:border-accent"
          />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span className="font-medium text-ink">{t.sahkopostiosoite}</span>
          <input
            type="email"
            value={contactEmail}
            onChange={(e) => setContactEmail(e.target.value)}
            className="rounded-md border border-line bg-paper-raised px-2 py-1.5 text-ink outline-none focus-visible:border-accent"
          />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span className="font-medium text-ink">{t.puhelin}</span>
          <input
            type="tel"
            value={contactPhone}
            onChange={(e) => setContactPhone(e.target.value)}
            className="rounded-md border border-line bg-paper-raised px-2 py-1.5 text-ink outline-none focus-visible:border-accent"
          />
        </label>
      </section>

      <AnimatedSection open={has("household_income") || has("assets") || has("household_size")}>
        <section className="flex flex-col gap-3 pt-1">
          <span id="household_income" />
          <span id="assets" />
          <span id="household_size" />
          <div>
            <h2 className="text-lg font-semibold text-ink">{t.ruokakuntaOtsikko}</h2>
            {required.find((f) => f.field === "household_size") && (
              <Causes field={required.find((f) => f.field === "household_size")!} />
            )}
          </div>
          <div className="flex flex-col gap-3">
            {members.map((member) => (
              <div key={member.key} className="grid grid-cols-2 gap-2 rounded-md border border-line p-3 sm:grid-cols-4">
                <label className="flex flex-col gap-1 text-sm">
                  <span className="text-ink-muted">{t.rooli}</span>
                  <select
                    value={member.role}
                    onChange={(e) => updateMember(member.key, { role: e.target.value as MemberIn["role"] })}
                    className="rounded-md border border-line bg-paper-raised px-2 py-1.5 text-ink outline-none focus-visible:border-accent"
                  >
                    {Object.entries(MEMBER_ROLE_LABELS).map(([value, label]) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="flex flex-col gap-1 text-sm">
                  <span className="text-ink-muted">{t.syntymavuosi}</span>
                  <input
                    type="number"
                    inputMode="numeric"
                    value={member.birth_year ?? ""}
                    onChange={(e) =>
                      updateMember(member.key, { birth_year: e.target.value ? Number(e.target.value) : null })
                    }
                    className="rounded-md border border-line bg-paper-raised px-2 py-1.5 text-ink outline-none focus-visible:border-accent"
                  />
                </label>
                {has("household_income") && (
                  <label className="flex flex-col gap-1 text-sm">
                    <span className="text-ink-muted">{t.bruttotulot}</span>
                    <input
                      type="number"
                      inputMode="numeric"
                      value={member.gross_monthly_income_eur ?? ""}
                      onChange={(e) => updateMember(member.key, { gross_monthly_income_eur: e.target.value || null })}
                      className="rounded-md border border-line bg-paper-raised px-2 py-1.5 text-ink outline-none focus-visible:border-accent"
                    />
                  </label>
                )}
                {has("assets") && (
                  <label className="flex flex-col gap-1 text-sm">
                    <span className="text-ink-muted">{t.varallisuus}</span>
                    <input
                      type="number"
                      inputMode="numeric"
                      value={member.assets_eur ?? ""}
                      onChange={(e) => updateMember(member.key, { assets_eur: e.target.value || null })}
                      className="rounded-md border border-line bg-paper-raised px-2 py-1.5 text-ink outline-none focus-visible:border-accent"
                    />
                  </label>
                )}
                <div className="flex items-end">
                  <button type="button" onClick={() => removeMember(member.key)} className="text-sm text-accent hover:underline">
                    {t.poistaHenkilo}
                  </button>
                </div>
              </div>
            ))}
          </div>
          <button type="button" onClick={addMember} className="w-fit text-sm font-medium text-accent hover:underline">
            {t.lisaaHenkilo}
          </button>
        </section>
      </AnimatedSection>

      <AnimatedSection open={has("housing_need")}>
        <section id="housing_need" className="flex flex-col gap-2 pt-1">
          <div>
            <h2 className="text-lg font-semibold text-ink">{t.asunnontarveOtsikko}</h2>
            {required.find((f) => f.field === "housing_need") && (
              <Causes field={required.find((f) => f.field === "housing_need")!} />
            )}
          </div>
          <label className="flex flex-col gap-1 text-sm">
            <span className="font-medium text-ink">{t.tilanne}</span>
            <select
              value={needSituation}
              onChange={(e) => setNeedSituation(e.target.value as NeedSituation)}
              className="w-fit rounded-md border border-line bg-paper-raised px-2 py-1.5 text-ink outline-none focus-visible:border-accent"
            >
              <option value="" />
              {Object.entries(NEED_SITUATION_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1 text-sm">
            <span className="font-medium text-ink">{t.kiireellisyysValinnainen}</span>
            <textarea
              value={needNote}
              onChange={(e) => setNeedNote(e.target.value)}
              rows={2}
              className="rounded-md border border-line bg-paper-raised px-2 py-1.5 text-ink outline-none focus-visible:border-accent"
            />
          </label>
        </section>
      </AnimatedSection>

      <AnimatedSection open={has("order_number")}>
        <section id="order_number" className="flex flex-col gap-2 pt-1">
          <div>
            <h2 className="text-lg font-semibold text-ink">{t.asumisoikeusnumeroOtsikko}</h2>
            {required.find((f) => f.field === "order_number") && (
              <Causes field={required.find((f) => f.field === "order_number")!} />
            )}
          </div>
          <label className="flex w-fit flex-col gap-1 text-sm">
            <span className="font-medium text-ink">{t.asumisoikeusnumero}</span>
            <input
              value={orderNumber}
              onChange={(e) => setOrderNumber(e.target.value)}
              className="rounded-md border border-line bg-paper-raised px-2 py-1.5 text-ink outline-none focus-visible:border-accent"
            />
          </label>
        </section>
      </AnimatedSection>

      <AnimatedSection open={has("deposit_acknowledged")}>
        <section id="deposit_acknowledged" className="flex flex-col gap-2 pt-1">
          <div>
            <h2 className="text-lg font-semibold text-ink">{t.vakuusOtsikko}</h2>
            {required.find((f) => f.field === "deposit_acknowledged") && (
              <Causes field={required.find((f) => f.field === "deposit_acknowledged")!} />
            )}
          </div>
          <label className="flex w-fit items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={depositAcknowledged}
              onChange={(e) => setDepositAcknowledged(e.target.checked)}
            />
            {t.hyvaksynVakuuden}
          </label>
        </section>
      </AnimatedSection>

      <AnimatedSection open={has("credit_record")}>
        <section id="credit_record" className="flex flex-col gap-2 pt-1">
          <div>
            <h2 className="text-lg font-semibold text-ink">{t.luottotiedotOtsikko}</h2>
            {required.find((f) => f.field === "credit_record") && (
              <Causes field={required.find((f) => f.field === "credit_record")!} />
            )}
          </div>
          <fieldset className="flex gap-4 text-sm">
            <legend className="mb-1 font-medium text-ink">{t.onkoMaksuhairioita}</legend>
            <label className="flex items-center gap-1.5">
              <input
                type="radio"
                name="credit_default"
                checked={creditDefaultFlag === true}
                onChange={() => setCreditDefaultFlag(true)}
              />
              {t.kylla}
            </label>
            <label className="flex items-center gap-1.5">
              <input
                type="radio"
                name="credit_default"
                checked={creditDefaultFlag === false}
                onChange={() => setCreditDefaultFlag(false)}
              />
              {t.ei}
            </label>
          </fieldset>
        </section>
      </AnimatedSection>

      <div className="flex flex-col gap-1.5 border-t border-line pt-4">
        <button
          type="button"
          onClick={onSave}
          disabled={saveState === "pending"}
          className="w-fit rounded-md bg-accent px-4 py-2.5 text-sm font-medium text-accent-ink hover:opacity-90 disabled:opacity-60"
        >
          {t.tallenna}
        </button>
        {saveMessage && (
          <p role={saveState === "error" ? "alert" : "status"} className="text-sm text-ink-muted">
            {saveMessage}
          </p>
        )}
      </div>
    </div>
  );
}

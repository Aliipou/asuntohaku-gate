import { notFound } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import { ApiError, getSimilarUnits, getUnit, getUnitViewings, type ViewingOut } from "@/lib/api";
import { parseLocale, pickTekstit, type Locale } from "@/lib/locale";
import { formatArea, formatDate, formatEuros } from "@/lib/format";
import { Gallery } from "@/components/Gallery";
import { Map } from "@/components/Map";
import { AddToApplicationButton } from "@/components/AddToApplicationButton";
import { ViewingBooker } from "@/components/ViewingBooker";
import { OfferForm } from "@/components/OfferForm";
import { SimilarUnitCard } from "@/components/SimilarUnitCard";
import { LocaleToggle } from "@/components/LocaleToggle";
import type { tekstit } from "@/lib/tekstit";

export const dynamic = "force-dynamic";

interface ListingPageProps {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ lang?: string }>;
}

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-3 border-b border-line py-1.5 text-sm last:border-0">
      <dt className="text-ink-muted">{label}</dt>
      <dd className="text-right tabular-nums text-ink">{value}</dd>
    </div>
  );
}

function boolLabel(value: boolean, t: typeof tekstit): string {
  return value ? t.kylla : t.ei;
}

export default async function ListingPage({ params, searchParams }: ListingPageProps) {
  const { id } = await params;
  const unitId = Number(id);
  const rawSearchParams = await searchParams;
  const locale: Locale = parseLocale(rawSearchParams.lang);
  const t = pickTekstit(locale);
  const langSuffix = locale === "en" ? "?lang=en" : "";

  if (!Number.isInteger(unitId)) {
    notFound();
  }

  let unit;
  try {
    unit = await getUnit(unitId);
  } catch (cause) {
    if (cause instanceof ApiError && cause.status === 404) {
      notFound();
    }
    return (
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6 sm:px-6">
        <p role="alert" className="rounded-md border border-line bg-paper-raised p-4 text-ink">
          {t.asunnonLataaminenEpaonnistui}
        </p>
      </main>
    );
  }

  const isSale = unit.listing_type === "myynti";
  const [similar, viewings] = await Promise.all([
    getSimilarUnits(unitId).catch(() => []),
    isSale ? getUnitViewings(unitId).catch((): ViewingOut[] => []) : Promise.resolve<ViewingOut[]>([]),
  ]);

  const description = locale === "en" && unit.description_en ? unit.description_en : unit.description_fi;
  const headlinePrice = isSale ? unit.price_eur : unit.rent_eur;

  return (
    <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-6 px-4 py-6 sm:px-6">
      <div className="flex items-center justify-between gap-3">
        <Link href={`/${langSuffix}`} className="text-sm text-ink-muted hover:underline">
          ← {t.takaisinHakuun}
        </Link>
        <LocaleToggle locale={locale} t={t} />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_20rem]">
        <div className="flex flex-col gap-6">
          <Gallery images={unit.images} t={t} />

          <div>
            <h1 className="text-2xl font-semibold text-ink">
              {unit.room_layout_fi} · {unit.property_name}
            </h1>
            <p className="text-ink-muted">
              {unit.street}, {unit.postal_code} {unit.city}
            </p>
            <p className="mt-2 tabular-nums text-3xl font-semibold text-ink">
              {headlinePrice ? formatEuros(headlinePrice) : t.eiTiedossa}
              {!isSale && <span className="ml-1 text-base font-normal text-ink-muted">/ {t.kuukausi}</span>}
            </p>
            <p className="mt-3 text-sm text-ink-muted">
              {unit.housing_form_label_fi} — {unit.housing_form_explanation_fi}{" "}
              <Link href={`/hakemus${langSuffix}`} className="font-medium text-accent hover:underline">
                {t.lueHakemuksesta}
              </Link>
            </p>
          </div>

          <dl className="rounded-lg border border-line bg-paper-raised p-4">
            <Fact label={t.sijainti} value={`${unit.street}, ${unit.city}`} />
            <Fact label={t.huoneistoselitelma} value={unit.room_layout_fi} />
            <Fact label={t.pintaAla} value={formatArea(unit.area_m2)} />
            <Fact label={t.kerrosFakta} value={String(unit.floor)} />
            {isSale ? (
              <>
                <Fact label={t.velatonHinta} value={unit.price_eur ? formatEuros(unit.price_eur) : t.eiTiedossa} />
                <Fact
                  label={t.hoitovastike}
                  value={unit.maintenance_fee_eur ? formatEuros(unit.maintenance_fee_eur) : t.eiTiedossa}
                />
              </>
            ) : (
              <>
                <Fact label={t.vuokra} value={unit.rent_eur ? formatEuros(unit.rent_eur) : t.eiTiedossa} />
                <Fact label={t.vakuus} value={unit.deposit_eur ? formatEuros(unit.deposit_eur) : t.eiTiedossa} />
              </>
            )}
            <Fact label={t.vapautuuFakta} value={unit.available_from ? formatDate(unit.available_from) : t.eiTiedossa} />
            <Fact label={t.rakennusvuosi} value={String(unit.built_year)} />
            <Fact label={t.hissi} value={boolLabel(unit.has_lift, t)} />
            <Fact label={t.saunaFakta} value={boolLabel(unit.has_sauna, t)} />
            <Fact label={t.parveke} value={boolLabel(unit.has_balcony, t)} />
            <Fact label={t.lemmikit} value={boolLabel(unit.pets_allowed, t)} />
            <Fact label={t.esteeton} value={boolLabel(unit.accessible, t)} />
          </dl>

          <p className="text-ink">{description}</p>

          <Map
            points={[
              {
                id: unit.id,
                lat: Number(unit.lat),
                lng: Number(unit.lng),
                label: headlinePrice ? formatEuros(headlinePrice) : t.eiTiedossa,
                title: `${unit.property_name}, ${unit.city}`,
              },
            ]}
            className="h-64 w-full overflow-hidden rounded-lg border border-line"
          />
        </div>

        <aside className="flex h-fit flex-col gap-4 rounded-lg border border-line bg-paper-raised p-4 lg:sticky lg:top-4">
          {unit.contact && (
            <div className="flex items-center gap-3">
              {unit.contact.photo_url && (
                <div className="relative h-12 w-12 shrink-0 overflow-hidden rounded-full">
                  <Image src={unit.contact.photo_url} alt="" fill sizes="48px" className="object-cover" unoptimized />
                </div>
              )}
              <div className="min-w-0">
                <p className="text-xs font-medium uppercase tracking-wide text-ink-muted">{t.yhteyshenkilo}</p>
                <p className="truncate font-medium text-ink">{unit.contact.name}</p>
                <p className="truncate text-sm text-ink-muted">{unit.contact.title_fi}</p>
              </div>
            </div>
          )}

          {unit.contact && (
            <div className="flex flex-col gap-1 text-sm">
              {unit.contact.phone && (
                <a href={`tel:${unit.contact.phone}`} className="text-accent hover:underline">
                  {t.soita}: {unit.contact.phone}
                </a>
              )}
              <a href={`mailto:${unit.contact.email}`} className="text-accent hover:underline">
                {t.lahetaSahkopostia}
              </a>
            </div>
          )}

          <hr className="border-line" />

          {isSale ? (
            <div className="flex flex-col gap-5">
              <div>
                <h2 className="mb-2 font-medium text-ink">{t.varaaNayttoaika}</h2>
                <ViewingBooker viewings={viewings} t={t} />
              </div>
              <div>
                <h2 className="mb-2 font-medium text-ink">{t.jataTarjous}</h2>
                <OfferForm unitId={unit.id} t={t} />
              </div>
            </div>
          ) : (
            <AddToApplicationButton unitId={unit.id} langSuffix={langSuffix} t={t} />
          )}
        </aside>
      </div>

      {similar.length > 0 && (
        <section className="flex flex-col gap-3">
          <h2 className="text-lg font-semibold text-ink">{t.vastaaviaAsuntoja}</h2>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
            {similar.map((s) => (
              <SimilarUnitCard key={s.id} unit={s} href={`/asunnot/${s.id}${langSuffix}`} t={t} />
            ))}
          </div>
        </section>
      )}
    </main>
  );
}

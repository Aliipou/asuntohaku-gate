import { notFound } from "next/navigation";
import Link from "next/link";
import { ApiError, getApplication, getRequiredFields } from "@/lib/api";
import { sovellusTekstit as t } from "@/lib/tekstitSovellus";
import { HakemusForm } from "@/components/HakemusForm";

export const dynamic = "force-dynamic";

interface HakemusPageProps {
  params: Promise<{ token: string }>;
}

/** Hakemus — the basket and the adaptive form (spec section 7, screen 3). Finnish only. */
export default async function HakemusPage({ params }: HakemusPageProps) {
  const { token } = await params;

  let application;
  let required;
  try {
    [application, required] = await Promise.all([getApplication(token), getRequiredFields(token)]);
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
      <h1 className="mb-4 text-2xl font-semibold text-ink">{t.hakemuksenOtsikko}</h1>
      {application.expired && application.units.length > 0 && (
        <p role="alert" className="mb-4 rounded-md border border-line bg-paper-raised p-3 text-sm text-ink">
          <Link href={`/hakemus/${token}/paatokset`} className="font-medium text-accent hover:underline">
            {t.katsoPaatokset}
          </Link>
        </p>
      )}
      <HakemusForm token={token} initialApplication={application} initialRequired={required} />
    </main>
  );
}

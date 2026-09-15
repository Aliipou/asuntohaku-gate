# asuntohaku-gate

Suomeksi lyhyesti: asuntohaku- ja hakemusdemo suomalaiselle yleishyödylliselle
asuntotoimijalle. Backend, sääntömoottori ja kaikki viisi näyttöä (haku, kohdesivu,
hakemus, päätökset, asukasvalinta) on rakennettu ja julkaistu. Kaikki tiedot ovat
keksittyjä — ks. [Live demo](#live-demo) ja [What is not built yet](#what-is-not-built-yet).

A housing search and application demo for a Finnish non-profit housing operator that
rents and sells apartments across four regulated housing forms. The hard part is not
the listings — it is deciding who is eligible for which apartment, and being able to
explain every decision to the applicant in Finnish.

## Live demo

- **Search + listings:** https://asuntohaku-gate-web.vercel.app
- **API:** https://asuntohaku-gate.vercel.app (`/api/health`, `/api/units`, ...)

Deployed on Vercel as two projects (frontend and API, cross-origin — see
`api/app/main.py`'s CORS config), a free Neon Postgres (seeded with the same 48
synthetic units described below), no Redis yet. See
[What is not built yet](#what-is-not-built-yet) for what that leaves out.

## What is built today

- **Schema and migration** — ten tables, with the constraints that carry meaning
  declared in the DDL: the rent/price XOR on `units`, uniqueness on
  `(application_id, unit_id)` and `(viewing_id, application_id)`, cascade deletes,
  non-empty rule/message/evidence on `decisions`, and a `BEFORE INSERT` trigger that
  takes a row lock on the viewing before counting, so viewing capacity cannot be
  exceeded by two concurrent bookings.
- **Seed stock** — 8 properties, 40 rental and 8 sale apartments across Helsinki,
  Espoo, Vantaa and Tampere, covering all four housing forms.
- **Rule engine** — 14 rules across the four housing forms plus two cross-cutting
  ones. Rules are pure functions of `(application snapshot, apartment, limits)`; the
  evaluation moment is passed in, so no rule reads a clock, a session or a database.
- **Generated rule catalogue** — [`docs/saannot.md`](docs/saannot.md), rendered from
  rule metadata. `python -m api.catalogue --check` fails on drift, and CI runs it.
- **API** — the endpoint surface for search, the application and its basket, the
  adaptive-field endpoint, decisions, viewings, offers and the ranked applicant
  view.
- **Frontend** — `web/`, Next.js + TypeScript, all five screens from the spec:
  - **Asuntohaku** (`/`) — search with URL-encoded filter state, a MapLibre GL JS
    map linked to the result list by hover, and an English locale toggle.
  - **Asunnon sivu** (`/asunnot/[id]`) — gallery including the floor plan, the
    dense Finnish key-facts table, the named contact, and — for rentals,
    "Lisää hakemukseen"; for sale units, "Varaa näyttöaika" and "Jätä tarjous"
    instead. Also has the English locale.
  - **Hakemus** (`/hakemus/[token]`) — the basket and the adaptive form: a
    section only appears once a chosen apartment's rule requires it, and says
    which apartment and rule did that. Finnish only, deliberately (see
    `CLAUDE.md`).
  - **Päätökset** (`/hakemus/[token]/paatokset`) — one row per apartment,
    rendered exactly as the API returns it; a `puuttuvat_tiedot` row links back
    to the exact Hakemus field.
  - **Asukasvalinta** (`/admin/asunnot/[id]`) — ranked applicants and the basis
    for the order, unauthenticated, per its own router's docstring.
- **CI** — [`.github/workflows/ci.yml`](.github/workflows/ci.yml): a `backend`
  job (ruff, mypy strict, the catalogue drift check, the migration against an
  empty database, pytest with coverage) and a `web` job (eslint, `tsc`, vitest,
  `next build`), both against service containers where needed and no cloud
  credentials.

### Seeing it work

The eight demo scenarios from the specification run against the rule engine
without a database or a frontend:

```bash
python -m seeds.scenarios
```

Each one prints the fields the application form asks for, which chosen apartment
caused each field to appear, and every apartment's decision in Finnish with the
rule that produced it and the values that decided it.

### Three outcomes, and every one of them explained

An eligibility outcome is `kelpoinen`, `puuttuvat_tiedot` or `ei_kelpoinen`, and it
cannot be constructed without a rule id, a Finnish message written to the applicant,
and the values that decided it. There is no default path and no bypass — a rule that
cannot say what decided it raises instead of returning a bare yes or no.

Missing information is never a rejection. If the household income has not been given
yet, the answer is "we cannot decide", not "no".

## Honest limitations

- **All data is synthetic.** No real applicant, property or apartment data was used,
  and no address, rent or price here corresponds to anything that exists.
- **The income, wealth and rent-ratio thresholds are invented for this demo.** They
  live in [`seeds/limits.py`](seeds/limits.py) and are not current statutory figures,
  not from ARA, and not from any housing operator.
- **There is no authentication and no identification.** None is planned for the demo.
- **There is no document upload and no integration** with any housing register or
  external system.

## What is not built yet

**No Redis.** Upstash's free-tier marketplace integration needs the same
one-time terms-of-service click Neon did, and that one hasn't happened yet.
The app runs correctly without it — `api/app/cache.py` degrades to "cache
always misses, throttle never triggers" and `/api/health` reports
`"cache": "disabled"`, which is what the live deploy actually shows right
now.

**The Vercel routing/runtime risk this section used to warn about is now
verified, not just applied.** Dropping the `rewrites` block (the sibling
`rag-eval-gate` fix) and pinning no explicit Python runtime string both work:
`/api/...` routes correctly on the live deploy.

**A real bug this surfaced, now fixed:** the live deploy first 500'd on every
page. Both `app/page.tsx` and `app/asunnot/[id]/page.tsx` are Server
Components that were passing the whole `tekstit` translations object —
several of its fields are functions, e.g. `tulosMaara(n)`, `kuvaNumero(n,
total)` — as a prop straight into Client Components. Next.js can't serialize
a function across that boundary, so it threw at render time on every route
that used `SearchControls`, `SearchResults`, `LocaleToggle`, `Gallery`,
`ViewingBooker`, `OfferForm` or `AddToApplicationButton`. `tsc`, `eslint` and
`next build` all passed anyway — it's a runtime React error, not a type
error, and this genuinely was never exercised against a live deploy until
now, exactly as this section used to say. Fixed by having each of those
components take the plain `locale` string and call `pickTekstit(locale)`
itself, instead of receiving the already-computed object.

**Still only lightly clicked through.** Search and the unit detail page have
been hit live and render real seeded data end to end. Hakemus (the
adaptive-field application form), päätökset (decisions) and the admin
asukasvalinta screen have not — they don't pass `t` across a Server/Client
boundary the same way (Finnish-only, no locale toggle), so they're less
likely to hit the same class of bug, but nobody has driven a real application
through them against the live API yet.

**No Playwright run yet.** SPEC section 9 asks for one end-to-end pass —
search, add two apartments of different housing forms, fill the form, read
the decisions. Not written. Now that there's a live deploy, this no longer
needs a Postgres service container to run against — it could run against
the live URLs above.

## What is live and what is not

Everything above runs as real code against a real, provisioned Postgres — Redis
is the one piece still pending (see above). Nothing in this repository is a
mock standing in for a missing feature. What's live: search, the unit detail
page, and the API behind both. What's not: Redis, and the Playwright pass that
would confirm the rest of the flow (application, decisions, admin ranking)
end to end.

## Running the tests

```bash
python -m venv .venv && .venv/bin/pip install -e ".[dev]"
python -m pytest              # rule engine, seed stock, catalogue drift
python -m api.catalogue --check
ruff check . && mypy
```

The rule engine tests need no database and run anywhere. The API contract tests
need PostgreSQL and skip without it; set `TEST_DATABASE_URL` to run them.

The migration has been applied to a real PostgreSQL 18 instance and the full
suite — 250 tests (208 run, 42 skipped where they need infrastructure this
sandbox doesn't have — see above), including the viewing-capacity trigger
under two concurrency races — passes against it.

To bring up the local database and Redis:

```bash
docker compose up -d
export DATABASE_URL=postgresql+psycopg://asuntohaku:asuntohaku@localhost:5432/asuntohaku
alembic upgrade head
python -m seeds.load
```

For the frontend:

```bash
cd web
npm ci
npm run lint && npm run typecheck && npm test && npm run build
```

`npm run dev` expects the API at `NEXT_PUBLIC_API_BASE_URL` (default
`http://localhost:8000`), so run `uvicorn api.app.main:app --reload` against the
database above alongside it to click through the app locally.

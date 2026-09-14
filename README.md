# asuntohaku-gate

Suomeksi lyhyesti: asuntohaku- ja hakemusdemo suomalaiselle yleishyödylliselle
asuntotoimijalle. Backend, sääntömoottori ja kaikki viisi näyttöä (haku, kohdesivu,
hakemus, päätökset, asukasvalinta) on rakennettu. Kaikki tiedot ovat keksittyjä, eikä
sovellusta ole vielä julkaistu — ks. [Live demo](#live-demo) ja
[What is not built yet](#what-is-not-built-yet).

A housing search and application demo for a Finnish non-profit housing operator that
rents and sells apartments across four regulated housing forms. The hard part is not
the listings — it is deciding who is eligible for which apartment, and being able to
explain every decision to the applicant in Finnish.

## Live demo

Not deployed yet. See [What is not built yet](#what-is-not-built-yet) for exactly
what deploying it still needs.

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

**Nothing is deployed.** `vercel.json` is present but has never been run against
it; there is no Neon Postgres, no Upstash Redis, and no live URL. Deploying it is
three steps: `alembic upgrade head` and `python -m seeds.load` against a real
Postgres instance, then `vercel deploy` for `web/` and `api/index.py`.

**Known risk, found empirically on a sibling project, not yet verified here:**
Vercel's Python runtime is zero-config now — an explicit `"runtime": "python@..."`
version string (removed from `vercel.json` above) is no longer valid. Separately,
Vercel's `rewrites` behavior recently changed to forward the rewritten
*destination* path to the function rather than the original request path, which
can break a FastAPI app's internal routing when its own routes (like this one's,
all under `/api/...`) depend on the original URL surviving the rewrite. This
broke the otherwise-identical `vercel.json` pattern on the sibling `rag-eval-gate`
project and had to be fixed by dropping the rewrite entirely. Verify `/api/...`
actually routes correctly the first time this is deployed, and drop or adjust the
rewrite if it doesn't.

**The frontend has not been exercised against a live backend.** This was built and
verified in a sandbox with no Docker and therefore no local Postgres or Redis (the
same constraint the backend's own test suite works around — see "Running the
tests" below). Every screen passes `tsc`, `eslint` and `next build`, and the
pure/presentational logic (URL filter round-tripping, the adaptive form's
section-by-section behaviour, all three decision states, `formatEuros`/
`formatArea`/`formatDate`) has unit and component tests — but nobody has clicked
through a real search, added a real apartment to a real application, or watched a
real decision render against a running API. CI's `web` job builds and tests the
frontend in isolation; it does not run it against the `backend` job's database.

**No Playwright run yet.** SPEC section 9 asks for one end-to-end pass — search,
add two apartments of different housing forms, fill the form, read the decisions —
against the built app with a Postgres service container. Not written.

## What is live and what is not

Everything above runs as real code against a real (if not-yet-provisioned)
Postgres/Redis pair; nothing in this repository is a mock standing in for a
missing feature. What genuinely doesn't exist yet is the deployment itself, and
the one-time manual/Playwright pass that would confirm frontend and backend agree
once they're both actually running.

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

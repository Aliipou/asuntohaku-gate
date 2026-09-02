# asuntohaku-gate

**Keskeneräinen.** Tästä on toistaiseksi rakennettu tietokantarakenne, sääntömoottori
ja generoitu sääntöluettelo. Hakusivua, hakulomaketta ja päätösnäkymää ei ole vielä
olemassa. Kaikki tiedot ovat keksittyjä.

A housing search and application demo for a Finnish non-profit housing operator that
rents and sells apartments across four regulated housing forms. The hard part is not
the listings — it is deciding who is eligible for which apartment, and being able to
explain every decision to the applicant in Finnish.

> **Work in progress.** This README describes only what is built and running today.
> See [What is not built yet](#what-is-not-built-yet).

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
- **CI** — [`.github/workflows/ci.yml`](.github/workflows/ci.yml): ruff, mypy
  strict, the catalogue drift check, the migration against an empty database, and
  pytest with coverage, all against Postgres and Redis service containers and no
  cloud credentials.

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

**The whole frontend.** There are no pages: no search, no apartment page, no
application form, no decisions screen, no tenant-selection view. Nothing in this
repository serves a web page today, and nothing is deployed. `vercel.json` is
present but has never been used.

The English locale for the listings is also unbuilt: `units.description_en` is
empty on every row.

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
suite — 233 tests, including the viewing-capacity trigger under two concurrency
races — passes against it.

To bring up the local database and Redis:

```bash
docker compose up -d
export DATABASE_URL=postgresql+psycopg://asuntohaku:asuntohaku@localhost:5432/asuntohaku
alembic upgrade head
python -m seeds.load
```

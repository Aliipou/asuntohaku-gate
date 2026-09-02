# asuntohaku-gate — build specification

A housing search and application site where the hard part is not the listings,
it is deciding who is eligible for which apartment and being able to explain
every decision.

Target deployment: Vercel + Neon Postgres + Upstash Redis.
Repository: public on GitHub. All data synthetic.

---

## 1. Why this project exists

A Finnish non-profit housing operator rents and sells apartments across four
housing forms, each with a different tenant-selection regime:

| Form | Finnish | Selection basis |
|---|---|---|
| Free-financed rental | vapaarahoitteinen vuokra-asunto | Open to anyone. Rent-paying ability and credit record only. |
| Short-term interest subsidy | lyhyen korkotuen vuokra-asunto | Household income is checked. Housing need and wealth are not. |
| Needs-assessed / long-term subsidy | tarveharkintainen vuokra-asunto | Income, wealth and housing need are all assessed. Applicants are ranked against each other. |
| Right-of-occupancy | asumisoikeusasunto | Requires an order number issued by the state housing authority. No income limits. Applicants over 55 are exempt from the wealth limit. Selection follows order number. |

An applicant browsing the site sees one grid of apartments and has no way to
know which ones they can actually get, what documents they will be asked for,
or why an application was rejected. Staff, on the other side, have to rank
applicants for the needs-assessed stock and be able to justify the ranking.

**The product idea:** one application covering several apartments, where the
form asks only for what the chosen apartments actually require, every
apartment gets its own eligibility outcome, and every outcome names the rule
that produced it and the exact value that triggered it — in Finnish, to the
applicant, not just in a log.

This is the same contract as a batch-ingestion gate turned outward: a decision
is never a bare yes or no, it always carries its rule id and its evidence.

---

## 2. Hard constraints

Read these before writing code. They are the point of the project.

1. **A decision is never unexplained.** Every eligibility outcome carries a
   rule id, a Finnish message, and the input value that decided it. There is no
   code path that produces an outcome without all three.
2. **Three outcomes, not two.** `kelpoinen`, `puuttuvat tiedot`,
   `ei kelpoinen`. Missing information is never silently treated as a failure.
   If the applicant has not told us their household income yet, the answer is
   "we cannot decide", not "no".
3. **The rule engine is pure.** Rules are functions from a snapshot of the
   application to an outcome. No database access, no clock, no network inside a
   rule. Time and identity are passed in.
4. **The form is adaptive and this is user-visible.** Adding a needs-assessed
   apartment to the application makes the wealth and housing-need sections
   appear, with a line saying which apartment caused it. Removing it removes
   them again.
5. **The rule catalogue is generated, not hand-written.** `docs/saannot.md` is
   produced from rule metadata. CI fails if the committed copy differs from the
   generated one.
6. **No official figures are claimed.** All income and wealth thresholds live in
   one seed file, are clearly marked as invented for the demo, and are not
   presented as current statutory limits anywhere in the UI or the README.

---

## 3. Stack

Chosen to match the target employer's stack, not for convenience.

- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.x, Pydantic v2, Alembic.
  Deployed as Python functions under `/api` on Vercel.
- **Frontend:** Next.js (App Router), React, TypeScript, Tailwind.
- **Database:** PostgreSQL on Neon.
- **Cache / rate limit:** Redis on Upstash. Used for search result caching and
  for throttling application submissions per edit token. Do not invent other
  uses for it.
- **Tests:** pytest for the rule engine and API, Vitest for frontend units,
  one Playwright path covering search → basket → application → decisions.
- **Local:** docker-compose with Postgres and Redis so the repo runs without
  any cloud account.
- **Map:** MapLibre GL JS against a free tile source. This is the only mapping
  dependency; do not hand-roll a canvas map.

Do not add: authentication providers, ORM alternatives, state management
libraries, component libraries, or an LLM. None of them serve this brief.

---

## 4. Data model

Table names in English, user-facing strings in Finnish.

```
properties          id, name, street, postal_code, city, housing_form,
                    built_year, lat, lng

units               id, property_id, unit_number, rooms, floor, area_m2,
                    listing_type ('vuokra' | 'myynti'),
                    rent_eur | price_eur, deposit_eur, maintenance_fee_eur,
                    availability ('vapaa' | 'vapautuu' | 'sopimuksella'),
                    available_from, description_fi, description_en,
                    room_layout_fi ('2h + kk + s'), dwelling_type
                    ('kerrostalo' | 'rivitalo' | 'omakotitalo' | 'luhtitalo'),
                    has_lift, has_sauna, has_balcony, pets_allowed,
                    accessible

unit_images         id, unit_id, url, kind ('valokuva' | 'pohjapiirros'),
                    alt_fi, credit, sort_order

contacts            id, property_id, name, title_fi, email, phone, photo_url

favourites          id, session_key, unit_id, created_at

saved_searches      id, session_key, name, query_json, created_at

applications        id, edit_token (uuid, unguessable), status,
                    created_at, expires_at (created_at + 3 months),
                    contact_name, contact_email, contact_phone,
                    order_number (nullable, for right-of-occupancy)

household_members   id, application_id, role ('paahakija' | 'toinen' |
                    'muu'), birth_year, gross_monthly_income_eur,
                    assets_eur

housing_need        application_id, situation ('asunnoton' |
                    'irtisanottu' | 'ahtaasti' | 'ei_tarvetta'),
                    urgency_note

application_units   id, application_id, unit_id, preference_rank

decisions           id, application_unit_id, outcome, rule_id,
                    message_fi, evidence_json, decided_at

viewings            id, unit_id, starts_at, capacity
viewing_bookings    id, viewing_id, application_id, created_at

offers              id, unit_id, contact_name, contact_email,
                    amount_eur, message, created_at
```

Constraints that must exist in the schema, not only in application code:

- `application_units` is unique on `(application_id, unit_id)`.
- `viewing_bookings` is unique on `(viewing_id, application_id)`.
- A booking cannot be inserted once `viewings.capacity` is reached — enforce
  with a trigger or a serialisable transaction, and test it concurrently.
- `units.rent_eur` is non-null exactly when `listing_type = 'vuokra'`, and
  `price_eur` non-null exactly when `listing_type = 'myynti'`. Use a check
  constraint.
- Deleting an application cascades to its members, need, units and decisions.
- Deleting a unit cascades to its images and favourites.
- `unit_images` is unique on `(unit_id, sort_order)`, and every unit has at
  least one image row.
- `favourites` is unique on `(session_key, unit_id)`. There is no login, so a
  favourite belongs to an opaque browser-held key, not to a user.

---

## 5. The rule engine

`api/rules/` — one module per housing form plus a shared registry.

Each rule is declared with metadata that drives both the engine and the
generated documentation:

```python
@rule(
    id="TARVE-TULO-01",
    housing_forms=["tarveharkintainen"],
    requires=["household_income"],
    title_fi="Ruokakunnan tulot enintään tulorajan suuruiset",
)
def income_within_limit(
    snapshot: ApplicationSnapshot, unit: UnitSnapshot, limits: Limits
) -> Outcome: ...
```

`requires` is what makes the form adaptive: the frontend asks the API which
fields the current basket needs, and the answer is the union of `requires`
across every rule that applies to the chosen units. Do not hardcode this list
in the frontend.

An `Outcome` is:

```python
Outcome(
    outcome: Literal["kelpoinen", "puuttuvat_tiedot", "ei_kelpoinen"],
    rule_id: str,
    message_fi: str,       # written to the applicant, not to an operator
    evidence: dict,        # the values that decided it
)
```

### Rule catalogue to implement

Free-financed (`vapaarahoitteinen`) — open stock, minimal gate:

- `VAPAA-MAKSU-01` — declared income covers rent at the configured
  rent-to-income ratio. Income may be salary or benefits; the rule must not
  treat benefit income differently.
- `VAPAA-VAKUUS-01` — applicant has acknowledged the deposit.
- `VAPAA-LUOTTO-01` — a credit-record flag is present in the demo data. A
  default marker does not by itself produce `ei_kelpoinen`; it produces
  `puuttuvat_tiedot` with a message asking for an explanation. This asymmetry
  is deliberate and should be commented in the code.

Short-term subsidy (`lyhyt_korkotuki`) — income only:

- `LYHYT-TULO-01` — household gross income within the limit for the household
  size and municipality.
- `LYHYT-EI-VARALLISUUS-01` — a guard rule that asserts no wealth or need
  fields were consulted. It exists so that a regression that starts asking
  low-income applicants for wealth data fails a test.

Needs-assessed (`tarveharkintainen`) — income, wealth, need, and ranking:

- `TARVE-TULO-01` — household income within the limit.
- `TARVE-VARALLISUUS-01` — household assets within the limit.
- `TARVE-TARVE-01` — a housing-need situation has been stated.
- `TARVE-SIJOITUS-01` — ranking rule. Produces an ordinal, not a pass/fail:
  urgent need first, then lowest wealth, then lowest income. Ties broken by
  application timestamp, never randomly.

Right-of-occupancy (`asumisoikeus`):

- `ASO-JARJ-01` — an order number is present and well-formed.
- `ASO-JARJ-02` — ranking by order number, ascending.
- `ASO-VARALLISUUS-01` — wealth limit applies, **except** where every adult
  applicant is 55 or older, in which case the rule returns `kelpoinen` with an
  evidence field naming the exemption. Write the test for the boundary case at
  exactly 55.

Cross-cutting:

- `YLEIS-KOKO-01` — household size against apartment size, as a soft rule: too
  large a household for the apartment yields `ei_kelpoinen`; too small yields
  `kelpoinen` with a note.
- `YLEIS-VANHENTUNUT-01` — application older than three months is expired and
  all its decisions become `puuttuvat_tiedot` with a message pointing to the
  edit link.

Every rule needs a test table with at least: one clear pass, one clear fail,
one missing-input case, and one boundary case. That is the floor, not the
target.

---

## 6. API surface

```
GET  /api/units                     search: city, rooms, min/max rent or
                                    price, housing_form, listing_type,
                                    availability. Cached in Redis 60s.
GET  /api/units/{id}
POST /api/applications              creates, returns edit_token
GET  /api/applications/{token}
PUT  /api/applications/{token}      household, income, wealth, need,
                                    order number
POST /api/applications/{token}/units      add unit
DELETE /api/applications/{token}/units/{unit_id}
GET  /api/applications/{token}/required-fields
                                    union of `requires` for the basket
GET  /api/applications/{token}/decisions
                                    per unit: outcome, rule_id, message,
                                    evidence
GET  /api/units/{id}/viewings
POST /api/viewings/{id}/bookings
POST /api/units/{id}/offers         sale units only
GET  /api/admin/units/{id}/applicants
                                    ranked list with the ranking basis shown

GET  /api/units/{id}/similar        Vastaavia asuntoja: same city, comparable
                                    size and price
GET  /api/cities                    autocomplete source for the search bar
GET  /api/favourites                by session key
POST /api/favourites                add
DELETE /api/favourites/{unit_id}    remove
GET  /api/saved-searches            by session key
POST /api/saved-searches            store a named filter state
```

Search accepts the sort order the UI offers (`uusimmat`, `halvin`, `kallein`,
`suurin`) and returns the result count separately from the page, because the
UI shows the count above the list.

The session key for favourites and saved searches is an opaque value the
browser generates and sends. It is not a login and grants no access to
anything but that browser's own list.

No login. The admin view is at an unlinked path and the README says plainly
that access control is out of scope for the demo. Do not fake a login screen.

---

## 7. Screens

Finnish first. English is a secondary locale for the search and detail pages
only — do not half-translate the application flow.

**The governing rule for screens 1 and 2: copy the pattern, not the identity.**

Someone working at a Finnish housing operator sees Oikotie, Etuovi and
Vuokraovi every day. If the search page does not behave like those, they will
not read it as a design choice, they will read it as unfinished. So screens 1
and 2 follow the conventions of the category closely: layout, component
vocabulary, information hierarchy and Finnish label wording are all taken from
what the category has settled on.

What is not taken: no logo, brand colour, photograph or copy from any real
site. In particular, do not attempt a pixel imitation of avainasunnot.fi — a
half-finished copy of their own site reads worse than a clean neutral one.

Original design effort goes into screens 3, 4 and 5 instead, which is where
this project has something of its own to say.

1. **Asuntohaku** — the landing page *is* the search, with results already
   present. No marketing hero.

   - Search bar with location autocomplete, and a segmented control for
     *Vuokrattavat* / *Myytävät*.
   - Horizontal filter bar of chips — city, rooms, price range, housing form,
     availability — plus *Lisää hakuehtoja* for the rest.
   - **Filter state is encoded in the URL.** A filtered search is a link that
     can be shared, bookmarked and reloaded.
   - Result count and a sort dropdown (`Uusimmat`, `Halvin ensin`,
     `Kallein ensin`, `Suurin pinta-ala`).
   - Split view: result list beside a map with price pins. The two are linked —
     hovering a row highlights its pin.
   - Result cards carry a photo, the price in large type, and one dense
     metadata line: `2h + kk + s · 54,5 m² · 3. krs`. A favourite (heart)
     control, and *Tallenna haku*.
   - Rental and sale stock are distinguished structurally, not by badge colour
     alone: a rental row shows rent and deposit, a sale row shows price and
     maintenance fee.

2. **Asunnon sivu** — the listing page, also to category convention.

   - Image gallery, including the `pohjapiirros` (floor plan) as one of the
     image types.
   - Dense key-facts table using the standard Finnish labels: `Sijainti`,
     `Huoneistoselitelmä`, `Pinta-ala`, `Kerros`, `Vuokra` / `Velaton hinta`,
     `Hoitovastike`, `Vakuus`, `Vapautuu`, `Rakennusvuosi`, `Hissi`, `Sauna`,
     `Parveke`, `Lemmikit`, `Esteetön`.
   - Map, sticky action panel with a named contact person and their photo, and
     *Vastaavia asuntoja* at the foot of the page.
   - Primary action: *Lisää hakemukseen*. For sale units: *Varaa näyttöaika*
     and *Jätä tarjous*.
   - **One line, and only one:** under the housing-form row, a single sentence
     saying what this housing form asks of the applicant, linking to the
     application. The listing page must not turn into a lesson in housing law.

3. **Hakemus** — the basket and the adaptive form. When a section appears, the
   interface says which chosen apartment requires it. Progress is expressed as
   what is still missing, not as a percentage.

4. **Päätökset** — one row per chosen apartment with its outcome, the plain
   Finnish reason, and the value that decided it. A `puuttuvat_tiedot` row
   links back to the exact field. This screen is the product; give it the most
   design attention.

5. **Asukasvalinta** (admin) — for one apartment, the ranked applicants and
   the basis for the order. For needs-assessed stock, show why applicant A
   ranks above B on the three ranking dimensions.

### Design direction

Screens 1 and 2 inherit their direction from the category. The rules below
govern screens 3, 4 and 5, and settle anything the category does not.

- The audience is people looking for a home, often under time pressure and
  sometimes on a low income, reading regulated terms they did not choose to
  learn. For the application and decision screens the design job is legibility
  and calm, not persuasion.
- Do not use: all-caps eyebrow labels; arrows appended to button text; a
  percentage progress bar.
- Base palette: an off-white paper ground, a dark slate ink, and one cool
  structural blue for interactive elements. The three outcome states need three
  distinguishable treatments that survive greyscale and colour-blindness — use
  shape and label, with colour as reinforcement only.
- One sans family with proper Finnish diacritics, set at a generous size for
  body text. Numbers are data, so tabular figures throughout.
- Motion: one place only, the moment a section appears or disappears in the
  application form because the basket changed. Everything else is static.
- Quality floor without announcing it: responsive to mobile, visible keyboard
  focus, reduced motion respected, all form errors tied to their field.

Copy: active voice, sentence case, no apology in error states. Say what is
missing and where to fix it.

### Map

Use MapLibre GL JS with a free raster or vector tile source. Do not build a
custom canvas map. The map is not where this project's time is spent.


## 8. Seed data

**This is not a placeholder task, and it comes before the search UI.** A search
page laid out against thin data looks broken no matter how good the code is,
and that is where most demos die. Build the content first and lay out against
it.

Eight properties across Helsinki, Espoo, Vantaa and Tampere, covering all four
housing forms. Around forty rental units and eight sale units. Availability
mixed across `vapaa`, `vapautuu` and `sopimuksella`.

Requirements on the content, not just the row count:

- **At least three real photographs per unit**, from Unsplash or Pexels under a
  licence that permits this use. Store the source and photographer in
  `unit_images.credit` and honour the licence's attribution terms. One of the
  images per unit is a `pohjapiirros`.
- **Multi-sentence Finnish descriptions**, written per apartment. No generated
  filler, no repeated sentences, no Lorem.
- **Real coordinates**, distinct per property and correct for the street named,
  so the map does not stack every pin on one point.
- **Prices appropriate to the area.** A Helsinki two-room flat and a Tampere
  two-room flat must not carry the same rent, and regulated stock must be
  visibly cheaper than free-financed stock in the same city.
- A named contact person per property, with a photograph, for the listing
  page's action panel.
- `room_layout_fi` written the way the category writes it: `2h + kk + s`.

Then eight named demo scenarios, each a preloaded application reachable by a
link from the README, chosen so that each one lands on a different rule:

1. Single applicant, free-financed only — clean pass.
2. Same applicant adds a needs-assessed apartment — the form grows, two new
   sections appear, and the decisions screen now shows a mixed result.
3. Household income just over the needs-assessed limit — one rule fails, the
   free-financed apartment in the same basket still passes.
4. Wealth over the limit, applicants all 56 — right-of-occupancy passes on the
   exemption, needs-assessed fails on wealth. Same basket, different outcomes.
5. Right-of-occupancy chosen with no order number — `puuttuvat_tiedot`, not a
   rejection.
6. Credit default marker present — `puuttuvat_tiedot` with a request for
   context.
7. Five-person household applying for a studio — size rule rejects.
8. An application dated four months ago — expired, all outcomes reset with the
   edit link.

Every threshold used by these scenarios comes from `seeds/limits.py`, with a
comment at the top of the file stating the figures are invented for the demo.


## 9. Tests

- Rule engine: table-driven, every rule, pass / fail / missing / boundary.
- A property test asserting the invariant that no `Outcome` can be constructed
  without a rule id, a Finnish message and non-empty evidence.
- API contract tests for every endpoint including the 404 and expired-token
  paths.
- A concurrency test that two bookings cannot exceed viewing capacity.
- A test that `docs/saannot.md` matches the generated output.
- One Playwright run: search, add two apartments of different forms, fill the
  form, read the decisions.

Do not pad the count with trivial assertions. A test that only checks a
constructor does not belong here.

---

## 10. CI

GitHub Actions on push:

- ruff, mypy strict on `api/`
- pytest with coverage reported, no threshold gate
- tsc, eslint, vitest
- the rule-catalogue drift check
- Playwright on the built app against a Postgres service container

CI must run without any cloud credentials.

---

## 11. README

English body, with a short Finnish summary at the top. It must state, in its
own section and without hedging:

- All data is synthetic. No real applicant or property data was used.
- The income, wealth and rent-ratio thresholds are invented for the demo and
  are not current statutory figures.
- There is no authentication; the staff view is open and access control is out
  of scope.
- There is no identification, no document upload, and no integration with any
  housing register or external system.
- The listing photographs are stock images under their own licences, credited
  in the repository. They are not photographs of the apartments described, and
  the apartments do not exist.
- The search and listing pages deliberately follow the conventions of Finnish
  property portals. No brand identity, logo, photograph or copy is taken from
  any real site.
- What the project is actually demonstrating: an adaptive application form
  driven by a documented rule catalogue, and decisions that always carry their
  rule and their evidence.

Screenshot of the decisions screen at the top of the README, since that is the
screen that carries the idea.

---

## 12. Build order

Do not build the frontend first.

1. Schema, migrations, seed data, limits file.
2. Rule engine with the full test table. Nothing else until this is green.
3. Rule catalogue generator and its drift check.
4. API, contract tests.
4b. Listing content: images, contacts, coordinates, descriptions. Before any
   search UI is laid out.
5. Search and detail pages.
6. Application flow and the adaptive-field endpoint.
7. Decisions screen. Spend the design time here.
8. Viewings, offers, admin ranking view.
9. Playwright path, CI, README, deploy.

If time runs out, cut steps 8 and the English locale. Do not cut step 3 or the
README limitations section.

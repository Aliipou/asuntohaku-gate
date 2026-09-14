"""Load the seed properties and apartments into the database.

    python -m seeds.load

Idempotent: it clears the seeded stock and inserts it again, so running it twice
leaves the same rows. It does not touch applications.
"""

from __future__ import annotations

import datetime as dt
import os
import sys

from sqlalchemy import create_engine, delete
from sqlalchemy.orm import Session

from api.app.models import Contact, Property, Unit, UnitImage, Viewing
from seeds.data import PROPERTIES
from seeds.listings import PROPERTY_CONTACTS, PROPERTY_COORDINATES, UNIT_LISTINGS

#: Fixed reference point rather than dt.datetime.now(): a seed run must be
#: reproducible, and "viewings a week from whenever someone happened to run
#: this" is not a fact worth being non-deterministic about.
_SEED_TODAY = dt.date(2026, 9, 14)

#: Two upcoming showing times per sale unit (spec section 7: "For sale units:
#: Varaa näyttöaika and Jätä tarjous"). Capacities differ so the demo shows
#: both a normal and a nearly-full slot; no bookings are seeded against them.
_VIEWING_OFFSETS_AND_CAPACITY: tuple[tuple[int, int, int], ...] = (
    (5, 17, 6),  # 5 days out, 17:00, room for six
    (12, 10, 2),  # 12 days out, 10:00, a small slot
)


def load(session: Session) -> tuple[int, int]:
    """Replace the seeded stock. Returns (properties, units) inserted.

    The stock itself lives in seeds/data.py; the listing content that the search
    and detail pages render — photographs, the Finnish description, the facts a
    listing shows, the contact person and the corrected coordinates — lives in
    seeds/listings.py and is joined on (property name, unit number) here.
    """
    session.execute(delete(Property))
    session.flush()

    units = 0
    sale_units: list[Unit] = []
    for seed in PROPERTIES:
        coordinates = PROPERTY_COORDINATES.get(seed.name)
        prop = Property(
            name=seed.name,
            street=seed.street,
            postal_code=seed.postal_code,
            city=seed.city,
            housing_form=seed.housing_form,
            built_year=seed.built_year,
            lat=coordinates.lat if coordinates else seed.lat,
            lng=coordinates.lng if coordinates else seed.lng,
        )

        contact = PROPERTY_CONTACTS.get(seed.name)
        if contact is not None:
            prop.contacts.append(
                Contact(
                    name=contact.name,
                    title_fi=contact.title_fi,
                    email=contact.email,
                    phone=contact.phone,
                    photo_url=contact.photo_url,
                )
            )

        for unit_seed in seed.units:
            listing = UNIT_LISTINGS[(seed.name, unit_seed.unit_number)]
            unit = Unit(
                unit_number=unit_seed.unit_number,
                rooms=unit_seed.rooms,
                floor=unit_seed.floor,
                area_m2=unit_seed.area_m2,
                listing_type=unit_seed.listing_type,
                rent_eur=unit_seed.rent_eur,
                price_eur=unit_seed.price_eur,
                deposit_eur=unit_seed.deposit_eur,
                availability=unit_seed.availability,
                available_from=unit_seed.available_from,
                # The richer description from seeds/listings.py replaces the
                # one-line placeholder that data.py carries.
                description_fi=listing.description_fi,
                description_en=listing.description_en,
                maintenance_fee_eur=listing.maintenance_fee_eur,
                room_layout_fi=listing.room_layout_fi,
                dwelling_type=listing.dwelling_type,
                has_lift=listing.has_lift,
                has_sauna=listing.has_sauna,
                has_balcony=listing.has_balcony,
                pets_allowed=listing.pets_allowed,
                accessible=listing.accessible,
            )
            for image in listing.images:
                unit.images.append(
                    UnitImage(
                        url=image.url,
                        kind=image.kind,
                        alt_fi=image.alt_fi,
                        credit=image.credit,
                        sort_order=image.sort_order,
                    )
                )
            if unit_seed.listing_type == "myynti":
                sale_units.append(unit)
            prop.units.append(unit)
            units += 1
        session.add(prop)

    session.flush()  # obtain unit.id for the sale units' viewings below

    for unit in sale_units:
        for days_out, hour, capacity in _VIEWING_OFFSETS_AND_CAPACITY:
            starts_at = dt.datetime.combine(
                _SEED_TODAY + dt.timedelta(days=days_out), dt.time(hour=hour, tzinfo=dt.UTC)
            )
            session.add(Viewing(unit_id=unit.id, starts_at=starts_at, capacity=capacity))

    session.flush()
    return len(PROPERTIES), units


def main() -> int:
    url = os.environ.get("DATABASE_URL")
    if not url:
        print(
            "DATABASE_URL is not set. Start the local database with `docker compose up -d` "
            "and export\n"
            "  DATABASE_URL=postgresql+psycopg://asuntohaku:asuntohaku@localhost:5432/asuntohaku",
            file=sys.stderr,
        )
        return 1

    engine = create_engine(url)
    with Session(engine) as session, session.begin():
        properties, units = load(session)
    print(f"Loaded {properties} properties and {units} units.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

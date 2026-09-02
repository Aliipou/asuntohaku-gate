"""Load the seed properties and apartments into the database.

    python -m seeds.load

Idempotent: it clears the seeded stock and inserts it again, so running it twice
leaves the same rows. It does not touch applications.
"""

from __future__ import annotations

import os
import sys

from sqlalchemy import create_engine, delete
from sqlalchemy.orm import Session

from api.app.models import Property, Unit
from seeds.data import PROPERTIES


def load(session: Session) -> tuple[int, int]:
    """Replace the seeded stock. Returns (properties, units) inserted."""
    session.execute(delete(Property))
    session.flush()

    units = 0
    for seed in PROPERTIES:
        prop = Property(
            name=seed.name,
            street=seed.street,
            postal_code=seed.postal_code,
            city=seed.city,
            housing_form=seed.housing_form,
            built_year=seed.built_year,
            lat=seed.lat,
            lng=seed.lng,
        )
        for unit_seed in seed.units:
            prop.units.append(
                Unit(
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
                    description_fi=unit_seed.description_fi,
                )
            )
            units += 1
        session.add(prop)

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

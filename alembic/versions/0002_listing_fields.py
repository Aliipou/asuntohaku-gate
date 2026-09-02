"""Listing fields, images, contacts, favourites and saved searches

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-02

What the search and listing pages need in order to look like the category they
belong to: the facts a Finnish listing shows, the photographs, the named contact
person, and the two things a portal lets an anonymous visitor keep.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DWELLING_TYPES = ("kerrostalo", "rivitalo", "omakotitalo", "luhtitalo")
IMAGE_KINDS = ("valokuva", "pohjapiirros")


def _enum(*values: str, name: str) -> sa.Enum:
    return sa.Enum(*values, name=name, native_enum=False, create_constraint=True)


def upgrade() -> None:
    # Added with server defaults so the existing rows stay valid, then the
    # defaults are dropped: the application supplies these values, the database
    # should not quietly invent them for future inserts.
    op.add_column("units", sa.Column("maintenance_fee_eur", sa.Numeric(10, 2), nullable=True))
    op.add_column(
        "units",
        sa.Column("room_layout_fi", sa.String(60), nullable=False, server_default=""),
    )
    op.add_column(
        "units",
        sa.Column(
            "dwelling_type",
            _enum(*DWELLING_TYPES, name="dwelling_type"),
            nullable=False,
            server_default="kerrostalo",
        ),
    )
    for flag in ("has_lift", "has_sauna", "has_balcony", "pets_allowed", "accessible"):
        op.add_column(
            "units",
            sa.Column(flag, sa.Boolean(), nullable=False, server_default=sa.false()),
        )

    op.alter_column("units", "room_layout_fi", server_default=None)
    op.alter_column("units", "dwelling_type", server_default=None)
    for flag in ("has_lift", "has_sauna", "has_balcony", "pets_allowed", "accessible"):
        op.alter_column("units", flag, server_default=None)

    # A sale listing carries a hoitovastike; a rental does not.
    op.create_check_constraint(
        "ck_units_maintenance_fee",
        "units",
        "listing_type = 'myynti' OR maintenance_fee_eur IS NULL",
    )

    op.create_table(
        "unit_images",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("unit_id", sa.BigInteger(), nullable=False),
        sa.Column("url", sa.String(500), nullable=False),
        sa.Column("kind", _enum(*IMAGE_KINDS, name="image_kind"), nullable=False),
        sa.Column("alt_fi", sa.String(300), nullable=False),
        sa.Column("credit", sa.String(300), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["unit_id"], ["units.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("unit_id", "sort_order", name="uq_unit_images_order"),
        sa.CheckConstraint("length(url) > 0", name="ck_unit_images_url"),
    )
    op.create_index("ix_unit_images_unit_id", "unit_images", ["unit_id"])

    op.create_table(
        "contacts",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("property_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("title_fi", sa.String(120), nullable=False),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("phone", sa.String(40), nullable=True),
        sa.Column("photo_url", sa.String(500), nullable=True),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_contacts_property_id", "contacts", ["property_id"])

    op.create_table(
        "favourites",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("session_key", sa.String(64), nullable=False),
        sa.Column("unit_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["unit_id"], ["units.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_key", "unit_id", name="uq_favourites"),
    )
    op.create_index("ix_favourites_session_key", "favourites", ["session_key"])
    op.create_index("ix_favourites_unit_id", "favourites", ["unit_id"])

    op.create_table(
        "saved_searches",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("session_key", sa.String(64), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("query_json", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_saved_searches_session_key", "saved_searches", ["session_key"])


def downgrade() -> None:
    op.drop_table("saved_searches")
    op.drop_table("favourites")
    op.drop_table("contacts")
    op.drop_table("unit_images")
    op.drop_constraint("ck_units_maintenance_fee", "units", type_="check")
    for column in (
        "accessible",
        "pets_allowed",
        "has_balcony",
        "has_sauna",
        "has_lift",
        "dwelling_type",
        "room_layout_fi",
        "maintenance_fee_eur",
    ):
        op.drop_column("units", column)

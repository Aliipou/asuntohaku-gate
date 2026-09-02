"""Tenant selection view.

Unlinked, unauthenticated, and the README says so plainly. There is no login
screen here because faking one would suggest an access control that does not
exist.
"""

from __future__ import annotations

import datetime as dt
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from api.app.db import get_session
from api.app.models import Application, ApplicationUnit, Unit
from api.app.schemas import ApplicantRankingOut, EvidenceItem, RankedApplicantOut
from api.app.snapshots import application_snapshot, unit_label, unit_snapshot
from api.rules import registry
from api.rules.engine import decide_unit, rank_applicants
from api.texts import fi
from seeds.limits import DEMO_LIMITS

router = APIRouter(prefix="/api/admin", tags=["admin"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.get("/units/{unit_id}/applicants", response_model=ApplicantRankingOut)
def list_applicants(unit_id: int, session: SessionDep) -> ApplicantRankingOut:
    """Applicants for one apartment, in order, with the basis for the order shown."""
    unit = session.scalars(
        select(Unit).where(Unit.id == unit_id).options(selectinload(Unit.property))
    ).one_or_none()
    if unit is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=fi.unit_not_found())

    now = dt.datetime.now(dt.UTC)
    applications = session.scalars(
        select(Application)
        .join(ApplicationUnit, ApplicationUnit.application_id == Application.id)
        .where(ApplicationUnit.unit_id == unit_id)
        .options(selectinload(Application.members), selectinload(Application.housing_need))
        .order_by(Application.created_at, Application.id)
    ).all()

    snapshot_unit = unit_snapshot(unit)
    snapshots = {a.id: application_snapshot(a, evaluated_at=now) for a in applications}
    by_id = {a.id: a for a in applications}

    ranked = rank_applicants(list(snapshots.values()), snapshot_unit, DEMO_LIMITS)
    ranking_rule = ranked[0].rule_id if ranked else _declared_ranking_rule(unit)

    rows: list[RankedApplicantOut] = []
    for entry in ranked:
        application = by_id[entry.application_id]
        eligibility = decide_unit(snapshots[application.id], snapshot_unit, DEMO_LIMITS)
        rows.append(
            RankedApplicantOut(
                rank=entry.rank,
                application_id=entry.application_id,
                contact_name=application.contact_name,
                rule_id=entry.rule_id,
                message_fi=entry.message_fi,
                evidence=EvidenceItem.from_evidence(entry.evidence),
                eligibility=eligibility.outcome,
                eligibility_message_fi=eligibility.deciding.message_fi,
            )
        )

    return ApplicantRankingOut(
        unit_id=unit.id,
        unit_label=unit_label(unit),
        housing_form=unit.property.housing_form,  # type: ignore[arg-type]
        ranking_rule_id=ranking_rule,
        ranking_basis_fi=(
            registry.get_rule(ranking_rule).meta.description_fi if ranking_rule else None
        ),
        applicants=rows,
    )


def _declared_ranking_rule(unit: Unit) -> str | None:
    """The form's ranking rule, so the view can explain itself with no applicants yet."""
    for registered in registry.rules_for_form(unit.property.housing_form):
        if registered.meta.kind == "ranking_rule":
            return registered.meta.id
    return None

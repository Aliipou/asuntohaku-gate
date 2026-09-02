"""Turning an application in the database into decisions the applicant can read.

Reads rows, builds snapshots, calls the pure engine, and shapes the result for
the API. The engine is never given a session and never asked for the time.

The ``decisions`` table is an append-only record of what was decided and when,
written whenever the application changes. Reads always re-evaluate rather than
returning stored rows, because an application can expire without anyone touching
it and a stale answer on the decisions screen would be worse than no table.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from api.app.models import Application, ApplicationUnit, Decision, Unit
from api.app.schemas import DecisionOut, EvidenceItem, RuleOutcomeOut, jsonable
from api.app.snapshots import application_snapshot, unit_label, unit_snapshot
from api.rules import registry
from api.rules.engine import decide_unit
from api.rules.types import Limits, UnitDecision
from api.texts import fi


def _chosen_units(session: Session, application: Application) -> list[tuple[ApplicationUnit, Unit]]:
    rows = session.scalars(
        select(ApplicationUnit)
        .where(ApplicationUnit.application_id == application.id)
        .options(selectinload(ApplicationUnit.unit).selectinload(Unit.property))
        .order_by(ApplicationUnit.preference_rank, ApplicationUnit.id)
    ).all()
    return [(row, row.unit) for row in rows]


def evaluate(
    session: Session, application: Application, limits: Limits, now: dt.datetime
) -> list[tuple[ApplicationUnit, Unit, UnitDecision]]:
    snapshot = application_snapshot(application, evaluated_at=now)
    results = []
    for application_unit, unit in _chosen_units(session, application):
        decision = decide_unit(snapshot, unit_snapshot(unit), limits)
        results.append((application_unit, unit, decision))
    return results


def to_out(unit: Unit, decision: UnitDecision) -> DecisionOut:
    return DecisionOut(
        unit_id=unit.id,
        unit_label=unit_label(unit),
        housing_form=unit.property.housing_form,  # type: ignore[arg-type]
        outcome=decision.outcome,
        outcome_label_fi=fi.OUTCOME_LABELS[decision.outcome],
        deciding_rule_id=decision.deciding.rule_id,
        message_fi=decision.deciding.message_fi,
        evidence=EvidenceItem.from_evidence(decision.deciding.evidence),
        rules=[
            RuleOutcomeOut(
                rule_id=outcome.rule_id,
                rule_title_fi=registry.get_rule(outcome.rule_id).meta.title_fi,
                outcome=outcome.outcome,
                outcome_label_fi=fi.OUTCOME_LABELS[outcome.outcome],
                message_fi=outcome.message_fi,
                evidence=EvidenceItem.from_evidence(outcome.evidence),
            )
            for outcome in decision.all_outcomes
        ],
    )


def record(
    session: Session,
    results: list[tuple[ApplicationUnit, Unit, UnitDecision]],
    now: dt.datetime,
) -> None:
    """Append what was decided, for every rule, not only the deciding one."""
    for application_unit, _unit, decision in results:
        for outcome in decision.all_outcomes:
            session.add(
                Decision(
                    application_unit_id=application_unit.id,
                    outcome=outcome.outcome,
                    rule_id=outcome.rule_id,
                    message_fi=outcome.message_fi,
                    evidence_json=jsonable(dict(outcome.evidence)),
                    decided_at=now,
                )
            )


def evaluate_and_record(
    session: Session, application: Application, limits: Limits, now: dt.datetime
) -> list[DecisionOut]:
    results = evaluate(session, application, limits, now)
    record(session, results, now)
    return [to_out(unit, decision) for _au, unit, decision in results]

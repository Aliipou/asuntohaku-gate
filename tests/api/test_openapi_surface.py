"""The endpoint surface, checked against SPEC section 6.

This one needs no database: it asks the application what it exposes. It is here
so that a route being renamed or dropped fails immediately, even in an
environment where the database-backed contract tests skip.
"""

from __future__ import annotations

import pytest

from api.app.main import app

#: (method, path) exactly as SPEC section 6 lists them.
REQUIRED_ROUTES = {
    ("GET", "/api/units"),
    ("GET", "/api/units/{unit_id}"),
    ("POST", "/api/applications"),
    ("GET", "/api/applications/{token}"),
    ("PUT", "/api/applications/{token}"),
    ("POST", "/api/applications/{token}/units"),
    ("DELETE", "/api/applications/{token}/units/{unit_id}"),
    ("GET", "/api/applications/{token}/required-fields"),
    ("GET", "/api/applications/{token}/decisions"),
    ("GET", "/api/units/{unit_id}/viewings"),
    ("POST", "/api/viewings/{viewing_id}/bookings"),
    ("POST", "/api/units/{unit_id}/offers"),
    ("GET", "/api/admin/units/{unit_id}/applicants"),
}


def _routes() -> set[tuple[str, str]]:
    schema = app.openapi()
    return {
        (method.upper(), path)
        for path, operations in schema["paths"].items()
        for method in operations
    }


@pytest.mark.parametrize(("method", "path"), sorted(REQUIRED_ROUTES))
def test_specified_endpoint_exists(method: str, path: str) -> None:
    assert (method, path) in _routes()


def test_no_endpoint_exists_that_the_specification_did_not_ask_for() -> None:
    """Scope check: the only extra is a health endpoint, which is named here."""
    extra = _routes() - REQUIRED_ROUTES - {("GET", "/api/health")}

    assert extra == set()


def test_there_is_no_login_endpoint() -> None:
    """No authentication, and no fake login screen to imply one (SPEC section 6)."""
    paths = {path for _method, path in _routes()}

    assert not any(
        word in path.lower() for path in paths for word in ("login", "auth", "session", "token/")
    )


def test_decisions_response_always_carries_rule_message_and_evidence() -> None:
    """The section 2.1 invariant, held at the API contract level.

    A client must not be able to receive an outcome without the reason for it, so
    none of these fields may become optional.
    """
    schema = app.openapi()
    decision = schema["components"]["schemas"]["DecisionOut"]

    for field in ("outcome", "deciding_rule_id", "message_fi", "evidence", "rules"):
        assert field in decision["required"], field


def test_ranked_applicant_response_carries_its_basis() -> None:
    schema = app.openapi()
    ranked = schema["components"]["schemas"]["RankedApplicantOut"]

    for field in ("rank", "rule_id", "message_fi", "evidence"):
        assert field in ranked["required"], field


def test_api_description_does_not_claim_official_figures() -> None:
    """SPEC section 2.6: nothing may present the thresholds as statutory."""
    description = app.openapi()["info"]["description"].lower()

    assert "synthetic" in description
    assert "invented" in description
    assert "no authentication" in description

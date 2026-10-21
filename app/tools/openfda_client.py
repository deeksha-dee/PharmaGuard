
from typing import Any

import httpx


OPENFDA_EVENT_URL = "https://api.fda.gov/drug/event.json"


class OpenFDAError(Exception):
    """Raised when the openFDA request fails or returns invalid data."""


def normalize_report(report: dict[str, Any]) -> dict[str, Any]:
    """Convert an openFDA report into PharmaGuard's initial case format."""
    patient = report.get("patient") or {}

    products = patient.get("drug") or []
    reactions = patient.get("reaction") or []

    return {
        "report_id": report.get("safetyreportid"),
        "received_date": report.get("receiptdate"),
        "serious": report.get("serious"),
        "drugs": [
            {
                "name": drug.get("medicinalproduct"),
                "role_code": drug.get("drugcharacterization"),
            }
            for drug in products
        ],
        "reactions": [
            {
                "term": reaction.get("reactionmeddrapt"),
                "outcome_code": reaction.get("reactionoutcome"),
            }
            for reaction in reactions
        ],
        "source": "openFDA",
    }


def fetch_reports(limit: int = 10) -> list[dict[str, Any]]:
    """
    Fetch a small batch of public drug adverse-event reports.

    This first version intentionally avoids search filters so we
    can verify connectivity and response parsing before adding
    more complex query logic.
    """
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")

    try:
        response = httpx.get(
            OPENFDA_EVENT_URL,
            params={"limit": limit},
            timeout=30.0,
        )
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise OpenFDAError(f"Unable to fetch openFDA reports: {exc}") from exc

    results = payload.get("results")
    if not isinstance(results, list):
        raise OpenFDAError("Unexpected openFDA response: results is not a list")

    return [normalize_report(report) for report in results]

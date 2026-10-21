
import httpx
import pytest

from app.tools.openfda_client import (
    OpenFDAError,
    fetch_reports,
    normalize_report,
)


def test_normalize_report():
    raw_report = {
        "safetyreportid": "12345",
        "receiptdate": "20261020",
        "serious": "1",
        "patient": {
            "drug": [
                {
                    "medicinalproduct": "Example Medicine",
                    "drugcharacterization": "1",
                }
            ],
            "reaction": [
                {
                    "reactionmeddrapt": "Headache",
                    "reactionoutcome": "1",
                }
            ],
        },
    }

    result = normalize_report(raw_report)

    assert result["report_id"] == "12345"
    assert result["serious"] == "1"
    assert result["drugs"][0]["name"] == "Example Medicine"
    assert result["reactions"][0]["term"] == "Headache"
    assert result["source"] == "openFDA"


def test_normalize_report_handles_missing_fields():
    result = normalize_report({})

    assert result["report_id"] is None
    assert result["drugs"] == []
    assert result["reactions"] == []


def test_fetch_reports_rejects_invalid_limit():
    with pytest.raises(ValueError):
        fetch_reports(limit=0)


def test_fetch_reports_parses_response(monkeypatch):
    def mock_get(*args, **kwargs):
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "safetyreportid": "abc",
                        "patient": {
                            "drug": [],
                            "reaction": [],
                        },
                    }
                ]
            },
            request=httpx.Request("GET", "https://example.com"),
        )

    monkeypatch.setattr(
        "app.tools.openfda_client.httpx.get",
        mock_get,
    )

    reports = fetch_reports(limit=1)

    assert len(reports) == 1
    assert reports[0]["report_id"] == "abc"


def test_fetch_reports_handles_http_failure(monkeypatch):
    def mock_get(*args, **kwargs):
        request = httpx.Request("GET", "https://example.com")
        response = httpx.Response(500, request=request)
        response.raise_for_status()

    monkeypatch.setattr(
        "app.tools.openfda_client.httpx.get",
        mock_get,
    )

    with pytest.raises(OpenFDAError):
        fetch_reports(limit=1)

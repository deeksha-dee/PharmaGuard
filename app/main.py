
from fastapi import FastAPI, HTTPException, Query

from app.tools.openfda_client import OpenFDAError, fetch_reports

app = FastAPI(
    title="PharmaGuard",
    description="Agentic pharmacovigilance research assistant",
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "project": "PharmaGuard",
        "status": "running",
        "version": "0.1.0",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/reports/fetch")
def fetch_adverse_event_reports(
    limit: int = Query(default=10, ge=1, le=100)
):
    try:
        reports = fetch_reports(limit=limit)
        return {
            "source": "openFDA",
            "count": len(reports),
            "reports": reports,
        }
    except OpenFDAError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

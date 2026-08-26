"""FastAPI v0.1 HTTP adapter for the Product D workflow."""

from __future__ import annotations

import os
from typing import Any, Union

from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .data import DataContractError, DataLoadError
from .engagement import ReaderContextError
from .orchestration import run_catalog_generation


app = FastAPI(
    title="Riverside Marketing",
    version="0.1.0",
    description="HTTP adapter for the Riverside Books Product D workflow.",
)

_default_origins = "http://localhost:5173,http://127.0.0.1:5173"
_allowed_origins = [
    origin.strip()
    for origin in os.getenv("RIVERSIDE_ALLOWED_ORIGINS", _default_origins).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["content-type"],
)


@app.get("/health")
def health() -> dict[str, str]:
    """Return a minimal service health response."""

    return {"status": "ok", "service": "riverside-marketing"}


@app.post("/generate")
def generate(
    payload: Union[list[dict[str, Any]], dict[str, Any]] = Body(
        ...,
        description=(
            "A JSON array of catalog records, or an object with catalog and "
            "optional reader_context"
        ),
    ),
) -> dict[str, Any]:
    """Run legacy catalog generation and optional reader engagement selection."""

    reader_context = None
    if isinstance(payload, list):
        catalog = payload
    else:
        catalog = payload.get("catalog")
        reader_context = payload.get("reader_context")
        if not isinstance(catalog, list) or not all(
            isinstance(record, dict) for record in catalog
        ):
            raise HTTPException(
                status_code=422,
                detail="Request object must contain a catalog array of book records",
            )
        if reader_context is not None and not isinstance(reader_context, dict):
            raise HTTPException(
                status_code=422,
                detail="reader_context must be an object when provided",
            )

    try:
        return run_catalog_generation(
            catalog,
            reader_context=reader_context,
        ).as_dict()
    except DataContractError as exc:
        # A missing or unreadable server-side contract is not a client data
        # rejection and should not expose an internal traceback.
        raise HTTPException(
            status_code=500,
            detail="Product D data contract is unavailable",
        ) from exc
    except (DataLoadError, ReaderContextError) as exc:
        detail = str(exc)
        if isinstance(exc, ReaderContextError):
            detail = [
                {"path": issue.path, "message": issue.message}
                for issue in exc.errors
            ]
        raise HTTPException(status_code=422, detail=detail) from exc

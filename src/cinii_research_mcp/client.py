import logging
import os
import re
from typing import Annotated, Any, Literal

import httpx
from pydantic import Field, StringConstraints, validate_call

SEARCH_URL = "https://cir.nii.ac.jp/opensearch/v2"
API_URL = f"{SEARCH_URL}/articles"
RECORD_URL = "https://cir.nii.ac.jp/crid/"
SOURCE_URL = "https://support.nii.ac.jp/ja/cir/r_opensearch"
RECORD_SOURCE_URL = "https://support.nii.ac.jp/ja/cir/r_json"
Query = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
Limit = Annotated[int, Field(ge=1, le=50)]
Start = Annotated[int, Field(ge=1, le=10000)]
Crid = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^[0-9]{1,20}$")]
RecordKind = Literal[
    "all",
    "projectsAndProducts",
    "data",
    "articles",
    "books",
    "dissertations",
    "projects",
    "researchers",
]
RECORD_FIELDS = (
    "@type",
    "dc:title",
    "jpcoar:awardTitle",
    "foaf:Person",
    "creator",
    "researcher",
    "career",
    "institution",
    "resourceType",
    "projectIdentifier",
    "personIdentifier",
    "productIdentifier",
    "publication",
    "dc:date",
    "since",
    "until",
    "dc:creator",
    "dcterms:publisher",
    "prism:edition",
    "ndl:degreeName",
    "ndl:dateGranted",
    "degreeAwardInstitution",
    "format",
    "repository",
    "hostingInstitution",
    "dc:rights",
)


def _redact_api_query(record: logging.LogRecord) -> bool:
    # HTTPX logs query parameters at INFO, including the required application ID.
    args = record.args
    if isinstance(args, tuple) and len(args) == 5 and isinstance(url := args[1], httpx.URL):
        if url.host == "cir.nii.ac.jp" and "appid" in url.params:
            record.args = (args[0], url.copy_with(query=None), *args[2:])
    return True


logging.getLogger("httpx").addFilter(_redact_api_query)


async def _get_json(url: str, **params: str | int) -> httpx.Response:
    app_id = os.environ.get("CINII_APP_ID", "").strip()
    if not app_id:
        raise ValueError("Set CINII_APP_ID to your registered CiNii Web API application ID.")
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            response = await client.get(url, params={"appid": app_id, **params})
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404 and url.startswith(RECORD_URL):
                raise ValueError("CiNii could not find a record for that CRID.") from None
            raise ValueError(
                f"CiNii returned HTTP {exc.response.status_code}. Check the application ID "
                "for authentication errors, or retry later if the service is unavailable."
            ) from None
        except httpx.RequestError:
            raise ValueError("CiNii could not be reached. Retry later.") from None
    return response


def _record_crid(url: str) -> str | None:
    if url.startswith(RECORD_URL):
        value = url.removeprefix(RECORD_URL)
        if re.fullmatch(r"[0-9]{1,20}", value):
            return value
    return None


async def _search(kind: RecordKind, query: str, limit: int, start: int) -> dict[str, Any]:
    response = await _get_json(
        f"{SEARCH_URL}/{kind}", q=query, format="json", count=limit, start=start
    )
    try:
        payload = response.json()
        total = int(payload["opensearch:totalResults"])
        results = payload.get("items", [])
        if total < 0 or not isinstance(results, list) or len(results) > limit:
            raise ValueError
        items = [
            {
                "title": row["title"],
                "url": row["@id"],
                "crid": _record_crid(row["@id"]),
                "record_type": row.get("dc:type"),
                "authors": row.get("dc:creator", []),
                "publication": row.get("prism:publicationName"),
                "published": row.get("dc:date") or row.get("prism:publicationDate"),
                "identifiers": row.get("dc:identifier", []),
            }
            for row in results
        ]
    except (ValueError, TypeError, KeyError, AttributeError):
        raise ValueError("CiNii returned an unexpected OpenSearch response.") from None
    return {
        "items": items,
        "total": total,
        "next_start": start + len(items)
        if items and start + len(items) <= min(total, 10000)
        else None,
        "source_url": SOURCE_URL,
    }


@validate_call
async def search_articles(query: Query, limit: Limit = 10, start: Start = 1) -> dict[str, Any]:
    """Search CiNii Research for article metadata. Pass next_start to read the next page."""
    return await _search("articles", query, limit, start)


@validate_call
async def search_records(
    query: Query, kind: RecordKind = "all", limit: Limit = 10, start: Start = 1
) -> dict[str, Any]:
    """Search CiNii Research across all records or restrict to the specified record kind."""
    return await _search(kind, query, limit, start)


@validate_call
async def get_record(crid: Crid) -> dict[str, Any]:
    """Get selected CiNii Research metadata for a CRID returned by search."""
    url = f"{RECORD_URL}{crid}"
    response = await _get_json(f"{url}.json")
    try:
        payload = response.json()
        if not isinstance(payload.get("@type"), str) or not isinstance(payload.get("@id"), str):
            raise ValueError
    except (ValueError, AttributeError):
        raise ValueError("CiNii returned an unexpected record JSON-LD response.") from None
    return {
        "crid": crid,
        "url": url,
        "metadata": {field: payload[field] for field in RECORD_FIELDS if field in payload},
        "source_url": RECORD_SOURCE_URL,
    }

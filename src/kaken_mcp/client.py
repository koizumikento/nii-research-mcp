import logging
import os
import re
from typing import Annotated, Any
from xml.etree import ElementTree

import httpx
from pydantic import Field, StringConstraints, validate_call

API_URL = "https://kaken.nii.ac.jp/opensearch/"
RESEARCHER_API_URL = "https://nrid.nii.ac.jp/opensearch/"
PROJECT_URL = "https://kaken.nii.ac.jp/grant/"
RESEARCHER_URL = "https://nrid.nii.ac.jp/ja/nrid/"
Query = Annotated[str, Field(min_length=1, max_length=200, pattern=r"\S")]
Limit = Annotated[int, Field(ge=1, le=20)]
Start = Annotated[int, Field(ge=1, le=200000)]
ResearcherStart = Annotated[int, Field(ge=1, le=1000)]
ProjectNumber = Annotated[
    str, StringConstraints(strip_whitespace=True, pattern=r"^(?:[Jj][Pp])?[0-9][0-9A-Za-z]{5,15}$")
]


def _redact_api_query(record: logging.LogRecord) -> bool:
    # HTTPX logs the URL at INFO, and this API requires the credential in its query.
    args = record.args
    if isinstance(args, tuple) and len(args) == 5 and isinstance(url := args[1], httpx.URL):
        base_url = url.copy_with(query=None)
        if str(base_url) in (API_URL, RESEARCHER_API_URL):
            record.args = (args[0], base_url, *args[2:])
    return True


logging.getLogger("httpx").addFilter(_redact_api_query)


async def _request(url: str, **params: str | int) -> httpx.Response:
    app_id = os.environ.get("KAKEN_APP_ID", "").strip()
    if not app_id:
        raise ValueError("Set KAKEN_APP_ID to your registered NII Web API application ID.")
    async with httpx.AsyncClient(timeout=20) as client:
        try:
            response = await client.get(url, params={"appid": app_id, "rw": 20, **params})
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise ValueError(
                f"KAKEN returned HTTP {exc.response.status_code}. Check KAKEN_APP_ID "
                "and the service's usage limits."
            ) from None
        except httpx.RequestError:
            raise ValueError("KAKEN could not be reached. Retry later.") from None
    return response


async def _fetch_projects(start: int, **criteria: str) -> tuple[int, list[ElementTree.Element]]:
    response = await _request(API_URL, format="xml", st=start, **criteria)
    try:
        xml = response.content.decode("utf-8-sig")
        if "<!DOCTYPE" in xml:
            raise ValueError
        root = ElementTree.fromstring(xml)
        if root.tag.rsplit("}", 1)[-1] != "grantAwardList":
            raise ValueError
        total = int(root.findtext("{*}totalResults", "-1"))
        projects = root.findall("{*}grantAward")
        if total < 0 or len(projects) > 20 or any(not project.get("id") for project in projects):
            raise ValueError
    except (ValueError, ElementTree.ParseError):
        raise ValueError("KAKEN returned an unexpected OpenSearch XML response.") from None
    return total, projects


def _project_summary(project: ElementTree.Element) -> dict[str, Any]:
    project_id = project.attrib["id"]
    return {
        "project_id": project_id,
        "project_number": project.get("awardNumber"),
        "title": project.findtext("{*}summary/{*}title"),
        "url": f"{PROJECT_URL}{project_id}/",
    }


@validate_call
async def search_projects(query: Query, limit: Limit = 10, start: Start = 1) -> dict[str, Any]:
    """Search KAKEN research projects by keyword. Use next_start to read the next page."""
    total, projects = await _fetch_projects(start, kw=query)
    items = [_project_summary(project) for project in projects[:limit]]
    next_start = start + len(items)
    return {
        "items": items,
        "total": total,
        "next_start": next_start if items and next_start <= min(total, 200000) else None,
        "source_url": "https://kaken.nii.ac.jp/",
    }


@validate_call
async def get_project(project_number: ProjectNumber) -> dict[str, Any]:
    """Look up an exact KAKEN project or area number, optionally prefixed with JP."""
    number = project_number.upper().removeprefix("JP")
    total, projects = await _fetch_projects(1, qb=number)
    matches = []
    for project in projects:
        numbers = [project.get("awardNumber", "")]
        numbers.extend(
            value.get("awardNumber", "") for value in project.findall("{*}summary/{*}awardNumber")
        )
        if number not in {value.upper().removeprefix("JP") for value in numbers}:
            continue
        status = project.find("{*}summary/{*}projectStatus")
        period = project.find("{*}summary/{*}periodOfAward")
        matches.append(
            {
                **_project_summary(project),
                "project_number": project.get("awardNumber") or number,
                "institutions": [
                    element.text
                    for element in project.findall("{*}summary/{*}institution")
                    if element.text
                ],
                "status": status.get("statusCode") if status is not None else None,
                "start_fiscal_year": period.findtext("{*}startFiscalYear")
                if period is not None
                else None,
                "end_fiscal_year": period.findtext("{*}endFiscalYear")
                if period is not None
                else None,
            }
        )
    return {
        "project_number": number,
        "items": matches,
        "truncated": total > len(projects),
        "source_url": "https://kaken.nii.ac.jp/",
    }


@validate_call
async def search_researchers(
    name: Query,
    limit: Limit = 10,
    start: ResearcherStart = 1,
    affiliation: Query | None = None,
) -> dict[str, Any]:
    """Search KAKEN researchers by name and optionally by institution."""
    criteria = {"qg": name}
    if affiliation is not None:
        criteria["qh"] = affiliation
    response = await _request(RESEARCHER_API_URL, format="json", st=start, **criteria)
    try:
        payload = response.json()
        total = int(payload["totalResults"])
        researchers = payload.get("researchers", [])
        if total < 0 or not isinstance(researchers, list) or len(researchers) > 20:
            raise ValueError
        items = []
        for row in researchers[:limit]:
            researcher_id = row["accn"]
            if not isinstance(researcher_id, str) or not researcher_id:
                raise ValueError
            items.append(
                {
                    "researcher_id": researcher_id,
                    "names": row.get("name", {}).get("humanReadableValue", []),
                    "researcher_numbers": row.get("id:person:erad", []),
                    "orcid_ids": row.get("id:orcid", []),
                    "current_affiliations": row.get("affiliations:current", []),
                    "url": f"{RESEARCHER_URL}{researcher_id}/"
                    if re.fullmatch(r"[0-9]{13}", researcher_id)
                    else None,
                }
            )
    except (AttributeError, KeyError, TypeError, ValueError):
        raise ValueError("KAKEN returned an unexpected researcher search response.") from None
    next_start = start + len(items)
    return {
        "items": items,
        "total": total,
        "next_start": next_start if items and next_start <= min(total, 1000) else None,
        "source_url": "https://nrid.nii.ac.jp/",
    }

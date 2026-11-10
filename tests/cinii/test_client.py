import json

import httpx
import pytest
import respx

from cinii_research_mcp import get_record, search_articles, search_records
from cinii_research_mcp.client import API_URL, RECORD_URL, SEARCH_URL


@pytest.mark.asyncio
@respx.mock
async def test_page_and_errors_do_not_expose_app_id(monkeypatch, caplog) -> None:
    monkeypatch.setenv("CINII_APP_ID", "fixture-id")
    caplog.set_level("INFO", logger="httpx")
    route = respx.get(API_URL).mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "opensearch:totalResults": "2",
                    "items": [{"@id": "https://cir.nii.ac.jp/crid/123", "title": "試験論文"}],
                },
            ),
            httpx.Response(401, json={"error": "fixture-id"}),
        ]
    )
    result = await search_articles("試験", limit=1)
    assert route.calls[0].request.url.params["appid"] == "fixture-id"
    assert result["next_start"] == 2
    assert result["items"][0]["title"] == "試験論文"
    assert result["items"][0]["crid"] == "123"
    assert "fixture-id" not in json.dumps(result)
    with pytest.raises(ValueError, match="HTTP 401") as error:
        await search_articles("試験", start=2)
    assert "fixture-id" not in str(error.value)
    assert "HTTP Request" in caplog.text
    assert "fixture-id" not in caplog.text


@pytest.mark.asyncio
@respx.mock
@pytest.mark.parametrize("kind", ["all", "data", "books", "researchers", "projectsAndProducts"])
async def test_search_records_by_kind(monkeypatch, kind) -> None:
    monkeypatch.setenv("CINII_APP_ID", "fixture-id")
    url = f"{RECORD_URL}1390006432294648704"
    route = respx.get(f"{SEARCH_URL}/{kind}").respond(
        json={
            "opensearch:totalResults": "3",
            "items": [{"@id": url, "title": "検索結果", "dc:type": "Dataset"}],
        }
    )
    result = await search_records("試験", kind=kind, limit=1, start=2)
    assert dict(route.calls[0].request.url.params) == {
        "appid": "fixture-id",
        "q": "試験",
        "format": "json",
        "count": "1",
        "start": "2",
    }
    assert result["items"][0]["record_type"] == "Dataset"
    assert result["items"][0]["crid"] == "1390006432294648704"
    assert result["next_start"] == 3


@pytest.mark.asyncio
@respx.mock
async def test_get_record_returns_selected_json_ld_fields(monkeypatch) -> None:
    monkeypatch.setenv("CINII_APP_ID", "fixture-id")
    crid = "1390006432294648704"
    url = f"{RECORD_URL}{crid}"
    route = respx.get(f"{url}.json").respond(
        json={
            "@id": url,
            "@type": "Article",
            "dc:title": [{"@language": "ja", "@value": "試験論文"}],
            "publication": {"prism:publicationDate": "2022-01-01"},
            "description": [{"notation": [{"@value": "転載しない抄録"}]}],
        }
    )
    result = await get_record(crid)
    assert dict(route.calls[0].request.url.params) == {"appid": "fixture-id"}
    assert result["url"] == url
    assert result["metadata"]["publication"]["prism:publicationDate"] == "2022-01-01"
    assert "description" not in result["metadata"]


@pytest.mark.asyncio
@respx.mock
async def test_get_record_requires_crid_and_reports_missing_record(monkeypatch) -> None:
    monkeypatch.setenv("CINII_APP_ID", "fixture-id")
    route = respx.get(f"{RECORD_URL}123.json").respond(404)
    with pytest.raises(ValueError):
        await get_record("https://example.org/123")
    assert not route.called
    with pytest.raises(ValueError, match="could not find a record"):
        await get_record("123")

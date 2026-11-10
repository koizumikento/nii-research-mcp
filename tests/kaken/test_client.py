import json

import httpx
import pytest
import respx

from kaken_mcp import get_project, search_projects, search_researchers
from kaken_mcp.client import API_URL, RESEARCHER_API_URL


@pytest.mark.asyncio
@respx.mock
async def test_project_page_and_sanitized_error(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level("INFO", logger="httpx")
    monkeypatch.setenv("KAKEN_APP_ID", "fixture-app-id")
    route = respx.get(API_URL).mock(
        side_effect=[
            httpx.Response(
                200,
                text="""<grantAwardList xmlns="https://example.org/kaken"
                    xmlns:os="http://a9.com/-/spec/opensearch/1.1/">
                    <os:totalResults>3</os:totalResults>
                    <grantAward id="KAKENHI-PROJECT-24K00001" awardNumber="24K00001">
                        <summary xml:lang="ja"><title>研究課題</title></summary>
                    </grantAward>
                </grantAwardList>""",
            ),
            httpx.Response(403, text="fixture-app-id"),
        ]
    )
    result = await search_projects("検索", limit=1, start=2)
    assert dict(route.calls[0].request.url.params) == {
        "appid": "fixture-app-id",
        "kw": "検索",
        "format": "xml",
        "rw": "20",
        "st": "2",
    }
    assert result["items"][0]["title"] == "研究課題"
    assert result["next_start"] == 3
    assert "fixture-app-id" not in json.dumps(result)
    with pytest.raises(ValueError, match="HTTP 403") as error:
        await search_projects("検索", start=3)
    assert "fixture-app-id" not in str(error.value)
    assert "HTTP Request" in caplog.text
    assert "fixture-app-id" not in caplog.text


@pytest.mark.asyncio
@respx.mock
async def test_project_number_lookup_matches_nested_award_number(monkeypatch) -> None:
    monkeypatch.setenv("KAKEN_APP_ID", "fixture-app-id")
    route = respx.get(API_URL).respond(
        text="""<grantAwardList xmlns="https://example.org/kaken"
            xmlns:os="http://a9.com/-/spec/opensearch/1.1/">
            <os:totalResults>2</os:totalResults>
            <grantAward id="KAKENHI-PROJECT-24K00010" awardNumber="24K00010">
                <summary><title>別の研究課題</title></summary>
            </grantAward>
            <grantAward id="KAKENHI-PROJECT-24K00001">
                <summary xml:lang="ja">
                    <title>研究課題</title>
                    <awardNumber awardNumber="24K00001"/>
                    <institution>試験大学</institution>
                    <projectStatus statusCode="granted"/>
                    <periodOfAward>
                        <startFiscalYear>2024</startFiscalYear>
                        <endFiscalYear>2026</endFiscalYear>
                    </periodOfAward>
                </summary>
            </grantAward>
        </grantAwardList>"""
    )
    result = await get_project(" jp24k00001 ")
    assert dict(route.calls[0].request.url.params) == {
        "appid": "fixture-app-id",
        "qb": "24K00001",
        "format": "xml",
        "rw": "20",
        "st": "1",
    }
    assert result["project_number"] == "24K00001"
    assert result["truncated"] is False
    assert result["items"] == [
        {
            "project_id": "KAKENHI-PROJECT-24K00001",
            "project_number": "24K00001",
            "title": "研究課題",
            "url": "https://kaken.nii.ac.jp/grant/KAKENHI-PROJECT-24K00001/",
            "institutions": ["試験大学"],
            "status": "granted",
            "start_fiscal_year": "2024",
            "end_fiscal_year": "2026",
        }
    ]


@pytest.mark.asyncio
@respx.mock
async def test_search_researchers_by_name_and_affiliation(monkeypatch, caplog) -> None:
    monkeypatch.setenv("KAKEN_APP_ID", "fixture-app-id")
    caplog.set_level("INFO", logger="httpx")
    route = respx.get(RESEARCHER_API_URL).respond(
        json={
            "totalResults": 3,
            "researchers": [
                {
                    "accn": "1000012345678",
                    "name": {"humanReadableValue": [{"lang": "ja", "text": "試験 太郎"}]},
                    "id:person:erad": ["12345678"],
                    "affiliations:current": [
                        {
                            "affiliation:institution": {
                                "humanReadableValue": [{"lang": "ja", "text": "試験大学"}]
                            }
                        }
                    ],
                }
            ],
        }
    )
    result = await search_researchers("試験", affiliation="試験大学", limit=1, start=2)
    assert dict(route.calls[0].request.url.params) == {
        "appid": "fixture-app-id",
        "qg": "試験",
        "qh": "試験大学",
        "format": "json",
        "rw": "20",
        "st": "2",
    }
    assert result["items"][0]["names"] == [{"lang": "ja", "text": "試験 太郎"}]
    assert result["items"][0]["url"] == "https://nrid.nii.ac.jp/ja/nrid/1000012345678/"
    assert result["next_start"] == 3
    assert "HTTP Request" in caplog.text
    assert "fixture-app-id" not in caplog.text

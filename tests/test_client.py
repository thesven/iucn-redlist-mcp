from __future__ import annotations

import httpx
import pytest

from iucn_redlist_mcp.client import IucnClient, IucnError


def test_client_init() -> None:
    client = IucnClient(token="test-token", base_url="https://api.iucnredlist.org/api/v4/")
    assert client.base_url == "https://api.iucnredlist.org/api/v4"
    assert client.token == "test-token"


def test_fallback_iconic_species_no_token() -> None:
    client = IucnClient(token=None)
    # Search
    results = client.search_species("Polar Bear")
    assert len(results) >= 1
    assert results[0]["scientific_name"] == "Ursus maritimus"
    assert results[0]["category"] == "VU"

    # Assessment
    assessment = client.get_species_assessment("Ursus maritimus")
    assert assessment["category"] == "VU"
    assert assessment["population_trend"] == "Decreasing"

    # Threats
    threats = client.get_species_threats("Ursus maritimus")
    assert len(threats) >= 1
    assert "Habitat shifting" in threats[0]["title"]

    # Actions
    actions = client.get_conservation_actions("Ursus maritimus")
    assert len(actions) >= 1
    assert actions[0]["status"] == "In place"

    # Narrative
    narrative = client.get_species_narrative("Ursus maritimus")
    assert "Arctic Ocean" in narrative["geographic_range"]

    # Regional
    regional = client.get_regional_assessment("Ursus maritimus", "europe")
    assert regional["category"] == "VU"


def test_search_species_api() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/taxa/scientific_name")
        assert request.headers.get("Authorization") == "Bearer api-token"
        return httpx.Response(
            200,
            json={
                "taxa": [
                    {
                        "sis_id": 12345,
                        "scientific_name": "Loxodonta africana",
                        "main_common_name": "African Bush Elephant",
                        "red_list_category": {"code": "EN", "description": "Endangered"},
                    }
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    client = IucnClient(token="api-token", transport=transport)
    results = client.search_species("Loxodonta")
    assert len(results) == 1
    assert results[0]["scientific_name"] == "Loxodonta africana"
    assert results[0]["category"] == "EN"


def test_get_species_assessment_api() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "/taxa/scientific_name/" in request.url.path
        return httpx.Response(
            200,
            json={
                "sis_id": 12345,
                "scientific_name": "Loxodonta africana",
                "main_common_name": "African Bush Elephant",
                "red_list_category": {"code": "EN", "description": "Endangered"},
                "criteria": "A2b",
                "population_trend": {"description": "Decreasing"},
                "year_published": 2021,
                "assessment_id": 998877,
            },
        )

    transport = httpx.MockTransport(handler)
    client = IucnClient(token="api-token", transport=transport)
    res = client.get_species_assessment("Loxodonta africana")
    assert res["category"] == "EN"
    assert res["year_published"] == 2021


def test_get_species_threats_api() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "/threats/scientific_name/" in request.url.path
        return httpx.Response(
            200,
            json={
                "threats": [
                    {
                        "code": "5.1",
                        "title": "Poaching for ivory",
                        "timing": "Ongoing",
                        "severity": "Very Rapid Declines",
                    }
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    client = IucnClient(token="api-token", transport=transport)
    threats = client.get_species_threats("Loxodonta africana")
    assert len(threats) == 1
    assert threats[0]["code"] == "5.1"


def test_get_conservation_actions_api() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "/conservation_actions/scientific_name/" in request.url.path
        return httpx.Response(
            200,
            json={
                "conservation_actions": [
                    {"code": "1.1", "title": "Site/area protection", "status": "In place"}
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    client = IucnClient(token="api-token", transport=transport)
    actions = client.get_conservation_actions("Loxodonta africana")
    assert len(actions) == 1
    assert actions[0]["title"] == "Site/area protection"


def test_get_species_narrative_api() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "/narratives/scientific_name/" in request.url.path
        return httpx.Response(
            200,
            json={
                "geographic_range": "Sub-Saharan Africa across savannas and forests.",
                "population": "Roughly 415,000 elephants remaining across the continent.",
            },
        )

    transport = httpx.MockTransport(handler)
    client = IucnClient(token="api-token", transport=transport)
    narrative = client.get_species_narrative("Loxodonta africana")
    assert "Sub-Saharan Africa" in narrative["geographic_range"]


def test_get_regional_assessment_api() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "/regions/europe" in request.url.path
        return httpx.Response(
            200,
            json={
                "red_list_category": {"code": "LC", "description": "Least Concern"},
                "criteria": None,
            },
        )

    transport = httpx.MockTransport(handler)
    client = IucnClient(token="api-token", transport=transport)
    res = client.get_regional_assessment("Canis lupus", "europe")
    assert res["category"] == "LC"


def test_api_error_handling() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="Internal Server Error")

    transport = httpx.MockTransport(handler)
    client = IucnClient(token="api-token", transport=transport)
    with pytest.raises(IucnError, match="IUCN API request failed"):
        client.get_species_assessment("Unknown species non-fallback")

    def handler_invalid_json(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"invalid-json{")

    client2 = IucnClient(token="api-token", transport=httpx.MockTransport(handler_invalid_json))
    with pytest.raises(IucnError, match="Invalid JSON"):
        client2.get_species_assessment("Unknown species non-fallback")

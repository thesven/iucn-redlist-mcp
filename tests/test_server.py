from __future__ import annotations

import httpx
import pytest

from iucn_redlist_mcp.client import IucnClient
from iucn_redlist_mcp.server import create_server


@pytest.fixture
def mock_client() -> IucnClient:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if "/taxa/scientific_name" in path:
            return httpx.Response(
                200,
                json={
                    "taxa": [
                        {
                            "sis_id": 1,
                            "scientific_name": "Panthera leo",
                            "main_common_name": "Lion",
                            "red_list_category": {"code": "VU", "description": "Vulnerable"},
                        }
                    ],
                    "scientific_name": "Panthera leo",
                    "red_list_category": {"code": "VU", "description": "Vulnerable"},
                    "criteria": "A2abcd",
                    "population_trend": {"description": "Decreasing"},
                    "year_published": 2016,
                },
            )
        if "/threats/" in path:
            return httpx.Response(
                200,
                json={"threats": [{"code": "2.1", "title": "Agriculture", "timing": "Ongoing"}]},
            )
        if "/conservation_actions/" in path:
            return httpx.Response(
                200,
                json={
                    "conservation_actions": [
                        {"code": "1.1", "title": "Site protection", "status": "In place"}
                    ]
                },
            )
        if "/narratives/" in path:
            return httpx.Response(
                200,
                json={"geographic_range": "Africa savanna", "population": "Roughly 20,000"},
            )
        return httpx.Response(404, text="Not Found")

    return IucnClient(token="mock-token", transport=httpx.MockTransport(handler))


@pytest.fixture
def failing_client() -> IucnClient:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="Server Error")

    return IucnClient(token="mock-token", transport=httpx.MockTransport(handler))


@pytest.mark.asyncio
async def test_server_tools(mock_client: IucnClient) -> None:
    server = create_server(mock_client)

    tools = await server.list_tools()
    tool_names = {t.name for t in tools}
    assert "search_species" in tool_names
    assert "get_species_assessment" in tool_names
    assert "get_species_threats" in tool_names
    assert "get_conservation_actions" in tool_names
    assert "get_species_narrative" in tool_names
    assert "get_regional_assessment" in tool_names

    res = await server.call_tool("search_species", {"query": "Lion"})
    assert "Panthera leo" in res.content[0].text

    res = await server.call_tool("get_species_assessment", {"scientific_name": "Panthera leo"})
    assert "Vulnerable" in res.content[0].text

    res = await server.call_tool("get_species_threats", {"scientific_name": "Panthera leo"})
    assert "Agriculture" in res.content[0].text

    res = await server.call_tool("get_conservation_actions", {"scientific_name": "Panthera leo"})
    assert "Site protection" in res.content[0].text

    res = await server.call_tool("get_species_narrative", {"scientific_name": "Panthera leo"})
    assert "Africa savanna" in res.content[0].text

    res = await server.call_tool(
        "get_regional_assessment",
        {"scientific_name": "Ursus maritimus", "region_identifier": "europe"},
    )
    assert "VU" in res.content[0].text


@pytest.mark.asyncio
async def test_server_tool_errors(failing_client: IucnClient) -> None:
    server = create_server(failing_client)

    res = await server.call_tool("search_species", {"query": "NonexistentRareCreature123"})
    assert "failed" in res.content[0].text

    res = await server.call_tool(
        "get_species_assessment", {"scientific_name": "NonexistentRareCreature123"}
    )
    assert "failed" in res.content[0].text

    res = await server.call_tool(
        "get_species_threats", {"scientific_name": "NonexistentRareCreature123"}
    )
    assert "failed" in res.content[0].text

    res = await server.call_tool(
        "get_conservation_actions", {"scientific_name": "NonexistentRareCreature123"}
    )
    assert "failed" in res.content[0].text

    res = await server.call_tool(
        "get_species_narrative", {"scientific_name": "NonexistentRareCreature123"}
    )
    assert "failed" in res.content[0].text

    res = await server.call_tool(
        "get_regional_assessment", {"scientific_name": "NonexistentRareCreature123"}
    )
    assert "failed" in res.content[0].text

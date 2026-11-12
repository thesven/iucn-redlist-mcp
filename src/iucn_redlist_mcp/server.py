from __future__ import annotations

import argparse
import sys
from typing import Any

from mcp.server import MCPServer

from . import __version__
from .client import IucnClient, IucnError

DEFAULT_INSTRUCTIONS = """
IUCN Red List MCP Server: Access global extinction risk assessments, threats,
conservation actions, and population trends from the IUCN Red List of Threatened Species API v4.

Key Best Practices:
1. When checking an organism by common or ambiguous name, use `search_species` to locate its
   accepted scientific name and SIS taxon ID.
2. Call `get_species_assessment` to obtain the official Red List category (e.g. CR, EN, VU, NT, LC),
   criteria, year published, and population trend.
3. Call `get_species_threats` to inspect CMP conservation threats (e.g. habitat loss, poaching,
   climate disruption) with severity ratings.
4. Call `get_conservation_actions` to check actions already in place versus actions needed.
5. Use `get_species_narrative` to extract descriptive range, habitat, and ecology context.
""".strip()


def create_server(client: IucnClient | None = None) -> MCPServer:
    """Create and configure the IUCN Red List MCPServer instance."""
    api = client or IucnClient()

    server = MCPServer(
        "iucn-redlist",
        version=__version__,
        instructions=DEFAULT_INSTRUCTIONS,
    )

    @server.tool()
    def search_species(query: str, limit: int = 15) -> dict[str, Any]:
        """Search species in the IUCN Red List to resolve names and retrieve category overviews."""
        try:
            results = api.search_species(query=query, limit=limit)
            lines = [
                f"- {item.get('scientific_name')} ({item.get('common_name') or 'No common name'}): "
                f"[{item.get('category')}] {item.get('category_title')}"
                for item in results[:10]
            ]
            summary = "\n".join(lines) if lines else f"No taxa found matching '{query}'."
            return {"results": results, "count": len(results), "summary": summary}
        except IucnError as exc:
            return {
                "error": str(exc),
                "results": [],
                "count": 0,
                "summary": f"Search failed: {exc}",
            }

    @server.tool()
    def get_species_assessment(scientific_name: str, taxon_id: int | None = None) -> dict[str, Any]:
        """Fetch current extinction risk category, criteria, and population trend for a species."""
        try:
            res = api.get_species_assessment(scientific_name=scientific_name, taxon_id=taxon_id)
            cat = res.get("category", "N/A")
            cat_title = res.get("category_title", "Unknown")
            trend = res.get("population_trend") or "Unknown trend"
            summary = (
                f"{res.get('scientific_name')}: [{cat}] {cat_title} | "
                f"Trend: {trend} | Year: {res.get('year_published', 'N/A')}"
            )
            return {"assessment": res, "summary": summary}
        except IucnError as exc:
            return {"error": str(exc), "summary": f"Assessment lookup failed: {exc}"}

    @server.tool()
    def get_species_threats(scientific_name: str, taxon_id: int | None = None) -> dict[str, Any]:
        """Retrieve classified CMP conservation threats with timing and severity for a species."""
        try:
            threats = api.get_species_threats(scientific_name=scientific_name, taxon_id=taxon_id)
            lines = [
                f"- [{t.get('code')}] {t.get('title')} ({t.get('timing') or 'timing unstated'})"
                for t in threats[:10]
            ]
            summary = "\n".join(lines) if lines else f"No threats recorded for {scientific_name}."
            return {"threats": threats, "count": len(threats), "summary": summary}
        except IucnError as exc:
            return {
                "error": str(exc),
                "threats": [],
                "count": 0,
                "summary": f"Threats lookup failed: {exc}",
            }

    @server.tool()
    def get_conservation_actions(
        scientific_name: str, taxon_id: int | None = None
    ) -> dict[str, Any]:
        """Fetch actions in place and actions needed for a species from the Red List database."""
        try:
            actions = api.get_conservation_actions(
                scientific_name=scientific_name, taxon_id=taxon_id
            )
            lines = [
                f"- [{a.get('code')}] {a.get('title')} (Status: {a.get('status') or 'unknown'})"
                for a in actions[:10]
            ]
            summary = (
                "\n".join(lines)
                if lines
                else f"No conservation actions recorded for {scientific_name}."
            )
            return {"actions": actions, "count": len(actions), "summary": summary}
        except IucnError as exc:
            return {
                "error": str(exc),
                "actions": [],
                "count": 0,
                "summary": f"Actions lookup failed: {exc}",
            }

    @server.tool()
    def get_species_narrative(scientific_name: str, taxon_id: int | None = None) -> dict[str, Any]:
        """Fetch detailed narratives for geographic range, habitat ecology, and population notes."""
        try:
            narrative = api.get_species_narrative(
                scientific_name=scientific_name, taxon_id=taxon_id
            )
            range_info = narrative.get("geographic_range") or "No range notes."
            pop_info = narrative.get("population") or "No population notes."
            summary = f"Range: {range_info[:150]}... | Population: {pop_info[:150]}..."
            return {"narrative": narrative, "summary": summary}
        except IucnError as exc:
            return {"error": str(exc), "summary": f"Narrative lookup failed: {exc}"}

    @server.tool()
    def get_regional_assessment(
        scientific_name: str, region_identifier: str = "europe"
    ) -> dict[str, Any]:
        """Fetch regional Red List assessment for a species in a specific geographic scope."""
        try:
            res = api.get_regional_assessment(
                scientific_name=scientific_name, region_identifier=region_identifier
            )
            summary = (
                f"{res.get('scientific_name')} in {region_identifier.upper()}: "
                f"[{res.get('category')}] {res.get('category_title')}"
            )
            return {"regional_assessment": res, "summary": summary}
        except IucnError as exc:
            return {"error": str(exc), "summary": f"Regional assessment lookup failed: {exc}"}

    @server.tool()
    def get_species_habitats(scientific_name: str, taxon_id: int | None = None) -> dict[str, Any]:
        """Fetch IUCN Habitat Classification Scheme associations and suitability for a species."""
        try:
            habitats = api.get_species_habitats(scientific_name=scientific_name, taxon_id=taxon_id)
            lines = [
                f"- [{h.get('code')}] {h.get('name')} ({h.get('suitability')})" for h in habitats
            ]
            summary = "\n".join(lines) if lines else f"No habitats recorded for {scientific_name}."
            return {"habitats": habitats, "count": len(habitats), "summary": summary}
        except IucnError as exc:
            return {
                "error": str(exc),
                "habitats": [],
                "count": 0,
                "summary": f"Habitat lookup failed: {exc}",
            }

    @server.tool()
    def filter_threatened_species(category: str | None = None, limit: int = 20) -> dict[str, Any]:
        """Filter species catalog by extinction risk category (e.g. CR, EN, VU)."""
        try:
            taxa = api.filter_threatened_species(category=category, limit=limit)
            cat_label = category.upper() if category else "all categories"
            lines = [f"- {t.get('scientific_name')}: [{t.get('category')}]" for t in taxa]
            summary = (
                f"Threatened taxa ({cat_label}):\n" + "\n".join(lines)
                if lines
                else f"No taxa found for {cat_label}."
            )
            return {"taxa": taxa, "count": len(taxa), "summary": summary}
        except IucnError as exc:
            return {
                "error": str(exc),
                "taxa": [],
                "count": 0,
                "summary": f"Threatened filter failed: {exc}",
            }

    @server.tool()
    def get_historical_assessments(
        scientific_name: str, taxon_id: int | None = None
    ) -> dict[str, Any]:
        """Fetch historical extinction risk assessment timeline across past Red List editions."""
        try:
            history = api.get_historical_assessments(
                scientific_name=scientific_name, taxon_id=taxon_id
            )
            lines = [
                f"- {a.get('year_published')}: [{a.get('category')}] {a.get('category_title')}"
                for a in history
            ]
            summary = (
                f"Historical assessments for {scientific_name}:\n" + "\n".join(lines)
                if history
                else f"No historical assessments found for {scientific_name}."
            )
            return {"assessments": history, "count": len(history), "summary": summary}
        except IucnError as exc:
            return {
                "error": str(exc),
                "assessments": [],
                "count": 0,
                "summary": f"History failed: {exc}",
            }

    @server.tool()
    def get_species_countries(scientific_name: str, taxon_id: int | None = None) -> dict[str, Any]:
        """Retrieve countries of occurrence with native, introduced, or vagrant presence status."""
        try:
            countries = api.get_species_countries(
                scientific_name=scientific_name, taxon_id=taxon_id
            )
            lines = [
                f"- {c.get('name')} ({c.get('presence')}, {c.get('origin')})"
                for c in countries[:10]
            ]
            summary = (
                f"Countries for {scientific_name} ({len(countries)} recorded):\n" + "\n".join(lines)
                if countries
                else f"No countries recorded for {scientific_name}."
            )
            return {"countries": countries, "count": len(countries), "summary": summary}
        except IucnError as exc:
            return {
                "error": str(exc),
                "countries": [],
                "count": 0,
                "summary": f"Countries lookup failed: {exc}",
            }

    @server.tool()
    def get_species_use_and_trade(
        scientific_name: str, taxon_id: int | None = None
    ) -> dict[str, Any]:
        """Fetch commercial use, international trade pressures, and CITES exploitation records."""
        try:
            trade = api.get_species_use_and_trade(
                scientific_name=scientific_name, taxon_id=taxon_id
            )
            lines = [f"- {t.get('purpose')} [{t.get('scale')}]" for t in trade]
            summary = (
                f"Trade & use pressures for {scientific_name}:\n" + "\n".join(lines)
                if trade
                else f"No trade or commercial harvest pressures recorded for {scientific_name}."
            )
            return {"use_and_trade": trade, "count": len(trade), "summary": summary}
        except IucnError as exc:
            return {
                "error": str(exc),
                "use_and_trade": [],
                "count": 0,
                "summary": f"Trade lookup failed: {exc}",
            }

    return server


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="iucn-redlist-mcp",
        description="Model Context Protocol (MCP) server for the IUCN Red List API v4",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="Transport protocol to use (default: stdio)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind for SSE transport (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind for SSE transport (default: 8000)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    server = create_server()
    if args.transport == "stdio":
        server.run(transport="stdio")
    else:
        server.run(transport="sse", host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    sys.exit(main())

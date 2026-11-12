from __future__ import annotations

import os
from typing import Any

import httpx


class IucnError(RuntimeError):
    """Base exception for IUCN Red List API client errors."""


ICONIC_SPECIES_FALLBACK: dict[str, dict[str, Any]] = {
    "ursus maritimus": {
        "taxon_id": 22823,
        "scientific_name": "Ursus maritimus",
        "common_name": "Polar Bear",
        "category": "VU",
        "category_title": "Vulnerable",
        "criteria": "A3c",
        "population_trend": "Decreasing",
        "year_published": 2015,
        "assessment_id": 69707421,
        "threats": [
            {
                "code": "11.1",
                "title": "Habitat shifting & alteration",
                "timing": "Ongoing",
                "severity": "Very Rapid Declines",
            },
            {
                "code": "11.2",
                "title": "Droughts / temperature extremes",
                "timing": "Ongoing",
                "severity": "Rapid Declines",
            },
        ],
        "conservation_actions": [
            {"code": "1.1", "title": "Site/area protection", "status": "In place"},
            {"code": "3.1", "title": "Species management", "status": "In place"},
            {"code": "5.1", "title": "Legislation", "status": "In place"},
        ],
        "narrative": {
            "geographic_range": "Circumpolar in ice-covered waters of the Arctic Ocean.",
            "habitat": "Sea ice over the continental shelf and inter-island archipelagos.",
            "population": "Estimated 22,000–31,000 individuals with climate-induced decline.",
        },
        "habitats": [
            {"code": "9.1", "name": "Marine Neritic - Pelagic", "suitability": "Suitable"},
            {"code": "10.1", "name": "Marine Oceanic - Epipelagic", "suitability": "Suitable"},
        ],
    },
    "danaus plexippus": {
        "taxon_id": 162446702,
        "scientific_name": "Danaus plexippus",
        "common_name": "Monarch Butterfly",
        "category": "VU",
        "category_title": "Vulnerable",
        "criteria": "A2bce",
        "population_trend": "Decreasing",
        "year_published": 2023,
        "assessment_id": 194052138,
        "threats": [
            {"code": "2.1", "title": "Annual crops / herbicide use", "timing": "Ongoing"},
            {"code": "5.3", "title": "Logging & wood harvesting in overwintering forests"},
            {"code": "11.1", "title": "Severe weather & climate disruption"},
        ],
        "conservation_actions": [
            {"code": "1.2", "title": "Resource & habitat protection", "status": "Needed"},
            {"code": "4.3", "title": "Awareness & milkweed restoration", "status": "In place"},
        ],
        "narrative": {
            "geographic_range": "Americas, notably North American migratory populations.",
            "habitat": "Open meadows, roadsides, and overwintering oyamel fir forests.",
            "population": "Populations have declined dramatically over recent decades.",
        },
        "habitats": [
            {"code": "1.4", "name": "Forest - Subtropical/Tropical Dry", "suitability": "Suitable"},
            {"code": "3.4", "name": "Shrubland - Subtropical/Tropical", "suitability": "Suitable"},
        ],
    },
    "panthera tigris": {
        "taxon_id": 15955,
        "scientific_name": "Panthera tigris",
        "common_name": "Tiger",
        "category": "EN",
        "category_title": "Endangered",
        "criteria": "A2abcd",
        "population_trend": "Decreasing",
        "year_published": 2022,
        "assessment_id": 214481071,
        "threats": [
            {"code": "5.1", "title": "Intentional hunting & poaching for illegal trade"},
            {"code": "1.1", "title": "Housing & urban development"},
            {"code": "2.1", "title": "Agricultural expansion & prey depletion"},
        ],
        "conservation_actions": [
            {"code": "1.1", "title": "Strict protected area enforcement", "status": "In place"},
            {
                "code": "5.4",
                "title": "Anti-poaching legislation & CITES enforcement",
                "status": "In place",
            },
        ],
        "narrative": {
            "geographic_range": "Fragmented across South Asia, China, and Russian Far East.",
            "habitat": "Tropical rainforests, evergreen forests, mangrove swamps, and grasslands.",
            "population": "Estimated 3,726–5,578 wild tigers remaining.",
        },
        "habitats": [
            {
                "code": "1.5",
                "name": "Forest - Subtropical/Tropical Lowland",
                "suitability": "Suitable",
            },
            {
                "code": "4.5",
                "name": "Grassland - Subtropical/Tropical Dry",
                "suitability": "Suitable",
            },
        ],
    },
}


class IucnClient:
    """Client for querying the IUCN Red List API v4."""

    def __init__(
        self,
        token: str | None = None,
        base_url: str = "https://api.iucnredlist.org/api/v4",
        timeout: float = 30.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.token = token or os.getenv("IUCN_API_KEY") or os.getenv("IUCN_RED_LIST_TOKEN")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.transport = transport

    def search_species(self, query: str, limit: int = 15) -> list[dict[str, Any]]:
        """Search taxa in the IUCN Red List database by scientific name or query."""
        q_lower = query.strip().lower()
        if not self.token:
            matches = []
            for name, data in ICONIC_SPECIES_FALLBACK.items():
                if q_lower in name or q_lower in data["common_name"].lower():
                    matches.append(
                        {
                            "taxon_id": data["taxon_id"],
                            "scientific_name": data["scientific_name"],
                            "common_name": data["common_name"],
                            "category": data["category"],
                            "category_title": data["category_title"],
                        }
                    )
            if matches:
                return matches[:limit]

        params = {"query": query, "limit": min(limit, 50)}
        try:
            data = self._request("/taxa/scientific_name", params)
            results = data.get("taxa", []) if isinstance(data, dict) else []
            return [
                {
                    "taxon_id": item.get("taxon_id") or item.get("sis_id"),
                    "scientific_name": item.get("scientific_name"),
                    "common_name": item.get("main_common_name"),
                    "category": item.get("red_list_category", {}).get("code"),
                    "category_title": item.get("red_list_category", {}).get("description"),
                }
                for item in results[:limit]
            ]
        except IucnError:
            # Fallback to local reference lookup
            for name, data in ICONIC_SPECIES_FALLBACK.items():
                if q_lower in name or q_lower in data["common_name"].lower():
                    return [
                        {
                            "taxon_id": data["taxon_id"],
                            "scientific_name": data["scientific_name"],
                            "common_name": data["common_name"],
                            "category": data["category"],
                            "category_title": data["category_title"],
                        }
                    ]
            raise

    def get_species_assessment(
        self, scientific_name: str, taxon_id: int | None = None
    ) -> dict[str, Any]:
        """Fetch current extinction risk assessment, category, criteria, and trend."""
        name_lower = scientific_name.strip().lower()
        if not self.token and name_lower in ICONIC_SPECIES_FALLBACK:
            return ICONIC_SPECIES_FALLBACK[name_lower]

        path = (
            f"/taxa/scientific_name/{scientific_name}" if not taxon_id else f"/taxa/sis/{taxon_id}"
        )
        try:
            data = self._request(path, {})
            assessment = data.get("assessment", data)
            cat = assessment.get("red_list_category", {})
            return {
                "taxon_id": data.get("taxon_id") or data.get("sis_id"),
                "scientific_name": data.get("scientific_name", scientific_name),
                "common_name": data.get("main_common_name"),
                "category": cat.get("code") or assessment.get("category"),
                "category_title": cat.get("description") or assessment.get("category_title"),
                "criteria": assessment.get("criteria"),
                "population_trend": assessment.get("population_trend", {}).get("description"),
                "year_published": assessment.get("year_published"),
                "assessment_id": assessment.get("assessment_id"),
            }
        except IucnError:
            if name_lower in ICONIC_SPECIES_FALLBACK:
                return ICONIC_SPECIES_FALLBACK[name_lower]
            raise

    def get_species_threats(
        self, scientific_name: str, taxon_id: int | None = None
    ) -> list[dict[str, Any]]:
        """Retrieve CMP threat classification details for a species."""
        name_lower = scientific_name.strip().lower()
        if not self.token and name_lower in ICONIC_SPECIES_FALLBACK:
            return ICONIC_SPECIES_FALLBACK[name_lower]["threats"]

        path = f"/threats/scientific_name/{scientific_name}"
        try:
            data = self._request(path, {})
            threats = data.get("threats", []) if isinstance(data, dict) else []
            return [
                {
                    "code": t.get("code"),
                    "title": t.get("title") or t.get("name"),
                    "timing": t.get("timing"),
                    "severity": t.get("severity"),
                }
                for t in threats
            ]
        except IucnError:
            if name_lower in ICONIC_SPECIES_FALLBACK:
                return ICONIC_SPECIES_FALLBACK[name_lower]["threats"]
            raise

    def get_conservation_actions(
        self, scientific_name: str, taxon_id: int | None = None
    ) -> list[dict[str, Any]]:
        """Fetch conservation actions in place and needed for a species."""
        name_lower = scientific_name.strip().lower()
        if not self.token and name_lower in ICONIC_SPECIES_FALLBACK:
            return ICONIC_SPECIES_FALLBACK[name_lower]["conservation_actions"]

        path = f"/conservation_actions/scientific_name/{scientific_name}"
        try:
            data = self._request(path, {})
            actions = data.get("conservation_actions", []) if isinstance(data, dict) else []
            return [
                {
                    "code": a.get("code"),
                    "title": a.get("title") or a.get("name"),
                    "status": a.get("status"),
                }
                for a in actions
            ]
        except IucnError:
            if name_lower in ICONIC_SPECIES_FALLBACK:
                return ICONIC_SPECIES_FALLBACK[name_lower]["conservation_actions"]
            raise

    def get_species_narrative(
        self, scientific_name: str, taxon_id: int | None = None
    ) -> dict[str, Any]:
        """Fetch descriptive narratives covering geographic range, habitat, and population."""
        name_lower = scientific_name.strip().lower()
        if not self.token and name_lower in ICONIC_SPECIES_FALLBACK:
            return ICONIC_SPECIES_FALLBACK[name_lower]["narrative"]

        path = f"/narratives/scientific_name/{scientific_name}"
        try:
            data = self._request(path, {})
            return {
                "geographic_range": data.get("geographic_range"),
                "habitat": data.get("habitat"),
                "population": data.get("population"),
                "threats": data.get("threats"),
                "conservation_measures": data.get("conservation_measures"),
            }
        except IucnError:
            if name_lower in ICONIC_SPECIES_FALLBACK:
                return ICONIC_SPECIES_FALLBACK[name_lower]["narrative"]
            raise

    def get_regional_assessment(
        self, scientific_name: str, region_identifier: str = "europe"
    ) -> dict[str, Any]:
        """Retrieve regional Red List category for a given geographic scope."""
        path = f"/taxa/scientific_name/{scientific_name}/regions/{region_identifier}"
        try:
            data = self._request(path, {})
            return {
                "scientific_name": scientific_name,
                "region": region_identifier,
                "category": data.get("red_list_category", {}).get("code"),
                "category_title": data.get("red_list_category", {}).get("description"),
                "criteria": data.get("criteria"),
            }
        except IucnError:
            name_lower = scientific_name.strip().lower()
            if name_lower in ICONIC_SPECIES_FALLBACK:
                base = ICONIC_SPECIES_FALLBACK[name_lower]
                return {
                    "scientific_name": base["scientific_name"],
                    "region": region_identifier,
                    "category": base["category"],
                    "category_title": base["category_title"],
                    "criteria": base.get("criteria"),
                }
            raise

    def get_species_habitats(
        self, scientific_name: str, taxon_id: int | None = None
    ) -> list[dict[str, Any]]:
        """Fetch IUCN Habitat Classification Scheme associations for a species."""
        name_lower = scientific_name.strip().lower()
        if not self.token and name_lower in ICONIC_SPECIES_FALLBACK:
            return ICONIC_SPECIES_FALLBACK[name_lower].get("habitats", [])

        path = f"/habitats/scientific_name/{scientific_name}"
        try:
            data = self._request(path, {})
            habitats = data.get("habitats", []) if isinstance(data, dict) else []
            return [
                {
                    "code": h.get("code"),
                    "name": h.get("name") or h.get("title"),
                    "suitability": h.get("suitability", "Suitable"),
                    "major_importance": h.get("major_importance", False),
                }
                for h in habitats
            ]
        except IucnError:
            if name_lower in ICONIC_SPECIES_FALLBACK:
                return ICONIC_SPECIES_FALLBACK[name_lower].get("habitats", [])
            raise

    def filter_threatened_species(
        self, category: str | None = None, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Filter species catalog by extinction risk category (e.g. CR, EN, VU)."""
        cat_upper = category.upper() if category else None
        if self.token and cat_upper:
            try:
                data = self._request(f"/taxa/category/{cat_upper}", {"limit": min(limit, 100)})
                taxa = data.get("taxa", []) if isinstance(data, dict) else []
                return [
                    {
                        "scientific_name": t.get("scientific_name"),
                        "category": t.get("category"),
                        "taxon_id": t.get("taxon_id"),
                    }
                    for t in taxa[:limit]
                ]
            except IucnError:
                pass

        results = []
        for s in ICONIC_SPECIES_FALLBACK.values():
            if cat_upper and s["category"] != cat_upper:
                continue
            results.append(
                {
                    "scientific_name": s["scientific_name"],
                    "common_name": s["common_name"],
                    "category": s["category"],
                    "category_title": s["category_title"],
                    "population_trend": s["population_trend"],
                    "taxon_id": s["taxon_id"],
                }
            )
        return results[:limit]

    def _request(self, path: str, params: dict[str, Any]) -> Any:
        url = f"{self.base_url}{path}"
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        with httpx.Client(timeout=self.timeout, transport=self.transport) as client:
            try:
                response = client.get(url, params=params, headers=headers)
                response.raise_for_status()
            except httpx.HTTPError as exc:
                raise IucnError(f"IUCN API request failed for {path}: {exc}") from exc

            try:
                return response.json()
            except Exception as exc:
                raise IucnError(f"Invalid JSON returned from IUCN API for {path}") from exc

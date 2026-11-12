# iucn-redlist-mcp

[![CI](https://github.com/thesven/iucn-redlist-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/thesven/iucn-redlist-mcp/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A dedicated, cross-taxa **Model Context Protocol (MCP)** server for the [IUCN Red List of Threatened Species API v4](https://api.iucnredlist.org/).

Fills a major gap in the ecological AI ecosystem by providing AI models and autonomous agents with direct, real-time access to global extinction risk categories, standardized CMP threat classifications, conservation actions in place, and population trend narratives across all kingdoms of life (animals, plants, fungi, and marine organisms).

---

## Key Features

- **Authoritative Red List Categories**: Retrieve global extinction risk statuses (`EX`, `EW`, `CR`, `EN`, `VU`, `NT`, `LC`, `DD`) along with specific assessment criteria and publication years.
- **IUCN Habitat Classification**: Query standardized habitat associations (forest, wetland, marine pelagic, shrubland) with suitability ratings.
- **CMP Threat Classifications**: Inspect standardized conservation threats (e.g., habitat loss, agricultural encroachment, poaching, climate disruption) alongside severity and timing.
- **Threatened Species Category Filter**: Filter species catalogs across threat categories (e.g. all CR taxa).
- **Conservation Actions Tracking**: Differentiate between conservation measures currently in place versus interventions required.
- **Ecological & Range Narratives**: Query detailed textual summaries of geographic distributions, habitat preferences, and population trends.
- **Multi-Scope & Regional Assessments**: Supports querying both global assessments and regional Red Lists (such as European and Mediterranean scopes).
- **Graceful Offline / Local Mode**: Contains built-in reference assessments for iconic species, enabling offline development and testing.

---

## Available Tools

| Tool | Description |
| :--- | :--- |
| `search_species` | Search taxa in the Red List database to resolve common/scientific names to SIS IDs. |
| `get_species_assessment` | Fetch the current Red List category, assessment criteria, year, and population trend. |
| `get_species_habitats` | Fetch standardized IUCN Habitat Classification Scheme associations and suitability. |
| `filter_threatened_species` | Filter species catalog by extinction risk category (e.g. `CR`, `EN`, `VU`). |
| `get_species_threats` | Retrieve classified CMP conservation threats with timing and severity. |
| `get_conservation_actions` | Retrieve conservation actions in place and actions needed. |
| `get_species_narrative` | Fetch descriptive narrative context (range, habitat ecology, and population notes). |
| `get_regional_assessment` | Retrieve regional Red List status for a specified geographic scope (e.g., `europe`). |

---

## Installation & Usage

### Running with `uvx` (Recommended)

```bash
# With optional IUCN API token
IUCN_API_KEY=your_token_here uvx --from git+https://github.com/thesven/iucn-redlist-mcp.git iucn-redlist-mcp

# Or in offline reference mode
uvx --from git+https://github.com/thesven/iucn-redlist-mcp.git iucn-redlist-mcp
```

### Claude Desktop Configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "iucn-redlist": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/thesven/iucn-redlist-mcp.git", "iucn-redlist-mcp"],
      "env": {
        "IUCN_API_KEY": "your_token_here"
      }
    }
  }
}
```

---

## Development & Quality Gate

```bash
# Run code formatting check
uv run ruff format --check src tests scripts

# Run linting
uv run ruff check src tests scripts

# Run test suite with strict coverage floor (>90%)
uv run pytest --cov=iucn_redlist_mcp --cov-branch --cov-report=term-missing

# Build wheel and sdist
uv build

# Run package distribution check & smoke test
uv run python scripts/check_dist.py
uv run python scripts/smoke.py
```

## License

MIT License. See [LICENSE](LICENSE) for details.

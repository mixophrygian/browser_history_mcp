# Browser History MCP Server

A Model Context Protocol (MCP) server that provides access to browser history data for analysis and insights. Built using the official [python mcp sdk](https://github.com/modelcontextprotocol/python-sdk) and intended for local integration with Claude Desktop, for personal use. 

## Features

- Query Firefox and/or Chrome browser history
- Group browsing sessions
- Categorize websites by type
- Analyze domain frequency
- Identify learning patterns
- Calculate productivity metrics

## Setup

### Automatic Setup (Recommended)

The server automatically detects your Firefox and Chrome profile directories based on your operating system:

- **macOS**: `~/Library/Application Support/Firefox/Profiles/[profile-id].default-release`
- **Linux**: `~/.mozilla/firefox/[profile-id].default-release`
- **Windows**: `%APPDATA%\Mozilla\Firefox\Profiles\[profile-id].default-release`

### Manual Configuration (if needed)

If automatic detection doesn't work, you can manually set the paths in `server.py`:

```python
FIREFOX_PROFILE_DIR = "/path/to/your/firefox/profile"
PATH_TO_FIREFOX_HISTORY = os.path.join(FIREFOX_PROFILE_DIR, "places.sqlite")
```

### Install Dependencies

This project uses `uv` for dependency management. If you don't have `uv` installed, you can install it with:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then install the project dependencies:

```bash
uv sync
```
 
This will create a virtual environment and install all dependencies from `pyproject.toml`.

Alternatively, if you prefer using pip:

```bash
pip install -e .
```

### Debug Locally
```bash
uv run mcp dev server.py
```
_Tip: Select the local url that allows you to open the inspector with the token pre-filled._

### Install the MCP for use in Claude Desktop
```bash
uv run mcp install server.py --name "Browser History MCP"
```

## Usage

The server provides several tools and prompts for analyzing browser history:

### Core Tools

- `detect_active_browser`: Detects which browser is currently active and provides recommendations for accessing history
- `get_browsing_insights`: Comprehensive analysis tool that retrieves history and performs multiple analyses in one call
- `analyze_browsing_sessions`: Group visits into sessions with time patterns, categories, and metrics
- `search_browser_history`: Search through cached browser history for specific queries
- `suggest_personalized_browser_categories`: Returns uncategorized URLs for custom categorization
- `test_browser_access`: Quick test to see what browser databases are accessible
- `diagnose_safari_support`: Diagnose Safari support and accessibility for debugging

### Analysis Prompts

- `productivity_analysis`: Creates a comprehensive productivity analysis prompt
- `learning_analysis`: Creates a deep learning pattern analysis prompt  
- `research_topic_extraction`: Extract and summarize research topics from browsing history

### Browser Support

The server supports Firefox, Chrome, and Safari browser history analysis. Note that browsers must be closed to access their history databases.

## Privacy

This tool accesses your browser history database directly. Ensure you understand the privacy implications and only use it in trusted environments.

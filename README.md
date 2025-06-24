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

The server provides several tools for analyzing browser history:

- `get_browser_history`: Retrieve history entries for a time period
- `detect_active_browser`: Tries to guess your preferred browser by seeing which one is currently active.  
- `group_browsing_history_into_sessions`: Group visits into sessions
- `categorize_browsing_history`: Categorize websites by type
- `analyze_domain_frequency`: Find most visited domains
- `find_learning_paths`: Identify learning patterns
- `calculate_productivity_metrics`: Calculate productivity ratios

## Privacy

This tool accesses your browser history database directly. Ensure you understand the privacy implications and only use it in trusted environments.

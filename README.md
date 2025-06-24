# Browser History MCP Server

A Model Context Protocol (MCP) server that provides access to browser history data for analysis and insights.

## Features

- Query Firefox browser history
- Group browsing sessions
- Categorize websites by type
- Analyze domain frequency
- Identify learning patterns
- Calculate productivity metrics

## Setup

### Automatic Setup (Recommended)

The server automatically detects your Firefox profile directory based on your operating system:

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

### Run the Server
```bash
python server.py
```

### Debug
```bash
uv run mcp dev server.py
```

## Security Notes

- Never commit your actual browser profile paths to version control
- Browser history databases contain sensitive information - handle with care
- The server automatically finds your profile, so no manual path configuration is needed

## Usage

The server provides several tools for analyzing browser history:

- `get_browser_history`: Retrieve history entries for a time period
- `group_browsing_history_into_sessions`: Group visits into sessions
- `categorize_browsing_history`: Categorize websites by type
- `analyze_domain_frequency`: Find most visited domains
- `find_learning_paths`: Identify learning patterns
- `calculate_productivity_metrics`: Calculate productivity ratios

## Privacy

This tool accesses your browser history database directly. Ensure you understand the privacy implications and only use it in trusted environments.

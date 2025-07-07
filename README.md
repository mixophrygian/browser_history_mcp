# Browser History MCP Server

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-1.9.3+-green.svg)](https://modelcontextprotocol.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)](https://github.com/yourusername/browser-mcp-server)

A powerful Model Context Protocol (MCP) server that provides comprehensive access to browser history data for analysis and insights. Built using the official [Python MCP SDK](https://github.com/modelcontextprotocol/python-sdk), this tool is designed for local integration with Claude Desktop for personal productivity analysis.

## 📋 Table of Contents

- [Features](#-features)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [API Reference](#-api-reference)
- [Browser Support](#-browser-support)
- [Privacy & Security](#-privacy--security)
- [Contributing](#-contributing)
- [License](#-license)

## ✨ Features

- 🔍 **Multi-Browser Support**: Query Firefox, Chrome, and (some versions of) Safari browser history
- 📊 **Session Analysis**: Group browsing sessions with intelligent time-based clustering
- 🏷️ **Smart Categorization**: Automatically categorize websites by type and purpose
- 📈 **Domain Analytics**: Analyze domain frequency and visit patterns
- 🎯 **Learning Insights**: Identify learning patterns and educational content consumption
- ⚡ **Productivity Metrics**: Calculate productivity scores and distraction analysis
- 🔄 **Real-time Access**: Direct database access for immediate insights
- 🛡️ **Privacy-First**: Local processing with no data transmission

## 🚀 Quick Start

1. **Install `uv` for dependency management**:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   uv sync
   ```

2. **Test locally**:
   ```bash
   uv run mcp dev server/main.py
   ```

3. **Install for Claude Desktop** (you will need to restart the app afterwards):
   ```bash
   uv run mcp install server/main.py --name "Browser History MCP"
   ```

## 📦 Installation

### Prerequisites

- Python 3.12 or higher
- Firefox, Chrome, or Safari browser
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Using uv (Recommended)

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and install
git clone https://github.com/yourusername/browser-mcp-server.git
cd browser-mcp-server
uv sync
```

### Using pip

```bash
git clone https://github.com/yourusername/browser-mcp-server.git
cd browser-mcp-server
pip install -e .
```

## ⚙️ Configuration

### Automatic Setup (Recommended)

The server automatically detects your browser profile directories:

| OS | Firefox Path | Chrome Path |
|---|---|---|
| **macOS** | `~/Library/Application Support/Firefox/Profiles/[profile-id].default-release` | `~/Library/Application Support/Google/Chrome/Default` |
| **Linux** | `~/.mozilla/firefox/[profile-id].default-release` | `~/.config/google-chrome/Default` |
| **Windows** | `%APPDATA%\Mozilla\Firefox\Profiles\[profile-id].default-release` | `%LOCALAPPDATA%\Google\Chrome\User Data\Default` |

### Manual Configuration

If automatic detection fails, manually configure paths in `server/main.py`:

```python
FIREFOX_PROFILE_DIR = "/path/to/your/firefox/profile"
CHROME_PROFILE_DIR = "/path/to/your/chrome/profile"
```

## 🎯 Usage

### Recommended Workflow

1. **Health Check**: `health_check` - Verify the MCP server is working
2. **Browser Status**: `check_browser_status` - See which browsers are available/locked
3. **Get Data**: `get_browser_history` - Retrieve raw browser history data
4. **Analyze**: `analyze_browser_history` - Choose analysis level:
   - `analysis_type="quick_summary"` - Basic stats (fastest)
   - `analysis_type="basic"` - Domain analysis and categorization
   - `analysis_type="comprehensive"` - Full analysis with sessions (default)

### Development Mode

```bash
uv run mcp dev server/main.py
```

**Pro tip**: Open the version of the local URL with the token pre-filled.  Then hit "Connect"

### Use with Claude Desktop

```bash
uv run mcp install server/main.py --name "Browser History MCP"
```

## 📚 API Reference

### Core Tools

| Tool | Description | Use Case |
|------|-------------|----------|
| `health_check` | Simple health check to test if the MCP server is working | Initial testing |
| `check_browser_status` | Step 1: Check which browsers are available and which are locked | Initial setup and troubleshooting |
| `get_browser_history` | Step 2: Get raw browser history data without analysis (fastest) | Quick data retrieval |
| `analyze_browser_history` | Step 3: Main analysis tool with options for quick_summary, basic, or comprehensive analysis | Full productivity analysis |
| `search_browser_history` | Search browser history for specific queries | Targeted research |
| `suggest_categories` | Get uncategorized URLs for custom categorization | Data organization |
| `diagnose_safari_support` | Safari support and accessibility diagnostics | Safari-specific issues |

### Analysis Prompts

| Prompt | Purpose | Output |
|--------|---------|--------|
| `productivity_analysis` | Comprehensive productivity assessment | Productivity metrics and recommendations |
| `learning_analysis` | Deep learning pattern analysis | Learning insights and progress tracking |
| `research_topic_extraction` | Research topic extraction and summarization | Research themes and focus areas |


## 🌐 Browser Support

| Browser | Status | Requirements |
|---------|--------|--------------|
| **Firefox** | ✅ Full Support | Browser must be closed |
| **Chrome** | ✅ Full Support | Browser must be closed |
| **Safari** | 🔄 Limited Support | Mostly older versions of Safari | 

**Important**: Browsers must be closed to access their history databases due to file locking mechanisms.

## 🔒 Privacy & Security

### Data Handling

- **Local Processing**: All data processing occurs locally on your machine
- **No Data Transmission**: No browser history data is sent to external servers (aside from whatever Claude desktop is doing)
- **Direct Database Access**: Reads directly from browser SQLite databases
- **Temporary Caching**: Optional local caching for performance

### Security Considerations

- Only use in trusted environments
- Ensure browser databases are not shared
- Review cached data regularly
- Close browsers before analysis

### Best Practices

1. **Close browsers** before running analysis
2. **Review permissions** for any MCP client integration
3. **Regular cleanup** of cached data if desired
4. **Monitor access** to browser history files

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/browser-mcp-server.git
cd browser-mcp-server

# Install development dependencies
uv sync

# Run tests
uv run pytest

# Format code
uv run black .
uv run isort .
```

### Reporting Issues

Please use the [GitHub Issues](https://github.com/yourusername/browser-mcp-server/issues) page to report bugs or request features.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.




---

**Note**: This tool is designed for personal use and local analysis. Please respect privacy and use responsibly.

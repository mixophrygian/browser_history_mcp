
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP

from local_types import HistoryEntryDict, CachedHistory, EnrichedSession, BrowserInsightsOutput
from browser_utils import tool_detect_active_browser, tool_get_browser_history, check_safari_accessibility, tool_search_browser_history, tool_test_browser_access
from prompts import PRODUCTIVITY_ANALYSIS_PROMPT, LEARNING_ANALYSIS_PROMPT, RESEARCH_TOPIC_EXTRACTION_PROMPT
from analysis_utils import tool_analyze_browsing_sessions, tool_get_browsing_insights, tool_suggest_personalized_browser_categories

CACHED_HISTORY = CachedHistory(history=[], time_period_in_days=0, browser_type="auto-detected")

mcp = FastMCP(name="Browser History MCP", instructions="This server makes it possible to query a user's Firefox, Chrome, or Safari browser history, analyze it, and create a thoughtful report with an optional lense of productivity or learning.")

@mcp.tool()
async def suggest_personalized_browser_categories() -> Dict[str, Any]:
    """Returns uncategorized URLs found in the cached browsing history.
    This tool is useful for suggesting categories for uncategorized URLs.
    Requires that @get_browsing_insights (or any other tool that populates the cache) has been executed first.
    Tell the user they can modify the browser categories in the BROWSING_CATEGORIES.py file.
    """
    return await tool_suggest_personalized_browser_categories(CACHED_HISTORY)


@mcp.prompt()
def productivity_analysis() -> str:
    """Creates a comprehensive productivity analysis prompt"""
    return PRODUCTIVITY_ANALYSIS_PROMPT


@mcp.prompt()
def learning_analysis() -> str:
    """Creates a deep learning pattern analysis prompt"""
    return LEARNING_ANALYSIS_PROMPT

@mcp.prompt()
def research_topic_extraction() -> str:
    """Extract and summarize research topics from browsing history"""
    return RESEARCH_TOPIC_EXTRACTION_PROMPT


@mcp.tool()
def detect_active_browser() -> Dict[str, Any]:
    """Detects which browser is currently active by attempting to connect to databases.
    Returns a dictionary with the following keys:
    - available_browsers: List of browser names that are available
    - active_browsers: List of browser names that are currently running
    - recommended_action: A message to the user about what to do to get the history
    Once we know which browser is active, we must tell the user that they will need to close the browser to get the history.
    Please remind them that they can restore their tabs by opening the browser again and possibly using Ctrl+Shift+T.
    """
    return tool_detect_active_browser()
    


async def get_browser_history(time_period_in_days: int, browser_type: Optional[str] = None, all_browsers: bool = False) -> List[HistoryEntryDict]:
    """Get browser history from the specified browser(s) for the given time period.
    
    Args:
        time_period_in_days: Number of days of history to retrieve
        browser_type: Browser type ('firefox', 'chrome', 'safari', or None for auto-detect)
        all_browsers: If True, get history from all available browsers. If False, use browser_type or auto-detect.
    """
    return await tool_get_browser_history(time_period_in_days, CACHED_HISTORY, browser_type, all_browsers)
    
@mcp.tool()
async def analyze_browsing_sessions(
    history_data: List[HistoryEntryDict], 
    max_gap_hours: float = 2.0,
) -> List[EnrichedSession]:
    """
    Comprehensive session analysis combining time patterns, categories, and metrics.
    Returns enriched session data that's easy for Claude to interpret and report on.
    """
    return await tool_analyze_browsing_sessions(history_data, max_gap_hours)
    

@mcp.tool()
def diagnose_safari_support() -> Dict[str, Any]:
    """Diagnose Safari support and accessibility. Useful for debugging Safari integration."""
    return check_safari_accessibility()



@mcp.tool()
async def get_browsing_insights(time_period_in_days: int = 7) -> BrowserInsightsOutput:
    """Analyze browsing history based on selected analysis types.
    This tool will get the browser history from the specified browser(s) for the given time period.
    It will then group the history into sessions, categorize the history, analyze the domains, find learning paths, and calculate productivity metrics.
    It will return a dictionary with the following keys:
    - enriched_sessions: List of browsing sessions
    - session_insights: Aggregated insights
    - categorized_data: Categorized browsing data
    - domain_stats: Domain statistics
    - learning_paths: Learning paths
    - productivity_metrics: Productivity metrics
    - report_helpers: Pre-formatted insights for easy report generation

    If the history is already cached, it will return the cached history.
    
    Args:
        history_data: List of history entries from get_browser_history
        analysis_types: List of analysis types to perform
    """
    return await tool_get_browsing_insights(time_period_in_days, CACHED_HISTORY)

@mcp.tool()
def test_browser_access() -> Dict[str, Any]:
    """Quick test to see what's accessible"""
    return tool_test_browser_access()


@mcp.tool()
async def search_browser_history(
    query: str,
) -> List[HistoryEntryDict]:
    """This tool can only be used after the tool @get_browsing_insights has been used to get the browser history, at least once.
    It will search the browser history for the query and return the results.
    """     

    return await tool_search_browser_history(query, CACHED_HISTORY)

        
if __name__ == "__main__":
    mcp.run()
#! /usr/bin/env python3

import time
from typing import Dict, List, Optional, Any, Union
from mcp.server.fastmcp import FastMCP

from local_types import HistoryEntryDict, CachedHistory
from browser_utils import tool_detect_available_browsers, tool_get_browser_history, check_safari_accessibility, tool_search_browser_history 
from prompts import PRODUCTIVITY_ANALYSIS_PROMPT, LEARNING_ANALYSIS_PROMPT, RESEARCH_TOPIC_EXTRACTION_PROMPT
from analysis_utils import tool_get_browsing_insights, tool_suggest_personalized_browser_categories, tool_get_quick_insights

CACHED_HISTORY = CachedHistory(history=[], time_period_in_days=0, browser_type="auto-detected")

mcp = FastMCP("browser-mcp-server")

@mcp.tool()
def check_browser_status() -> Dict[str, Any]:
    """Step 1: Check which browsers are available and which are locked.
    This is the first step in the workflow - run this to see if you need to close any browsers.
    
    Returns a dictionary with:
    - status: "ready", "browser_locked", or "error"
    - error_message: Clear error message if there's an issue
    - user_action_required: True if user needs to close browsers
    - recommended_action: Specific instructions for the user
    - available_browsers: List of detected browsers
    - active_browsers: List of browsers that are currently running
    
    IMPORTANT: If status is "browser_locked", you MUST tell the user to close the specified browser(s).

    """
    result = tool_detect_available_browsers()
    
    # If there's a user action required, make it very clear
    if result.get("user_action_required", False):
        result["claude_instruction"] = "IMPORTANT: Tell the user they need to close their browser(s) as specified in the recommended_action field."
    
    return result

@mcp.tool()
async def get_browser_history(time_period_in_days: int = 7, browser_type: Optional[str] = None, all_browsers: bool = True) -> Union[List[HistoryEntryDict], Dict[str, Any]]:
    """Step 2: Get raw browser history data without analysis. This is the fastest way to retrieve browser history and should be used before any analysis.
    
    Args:
        time_period_in_days: Number of days of history to retrieve (default: 7)
        browser_type: Browser type ('firefox', 'chrome', 'safari', or None for auto-detect)
        all_browsers: If True, get history from all available browsers (default: True)
    
    Returns:
        Either a list of history entries or a dictionary with partial results and browser status
    """
    return await tool_get_browser_history(time_period_in_days, CACHED_HISTORY, browser_type, all_browsers)

@mcp.tool()
async def analyze_browser_history(
    time_period_in_days: int = 7,
    analysis_type: str = "comprehensive",
    fast_mode: bool = True
) -> Dict[str, Any]:
    """Step 3: Analyze browser history with different levels of detail.
    
    This is the main analysis tool that consolidates all analysis options.
    
    Args:
        time_period_in_days: Number of days of history to analyze (default: 7)
        analysis_type: Type of analysis to perform:
            - "quick_summary": Basic stats only (fastest)
            - "basic": Domain analysis and categorization (not yet implemented)
            - "comprehensive": Full analysis with sessions and insights (default)
        fast_mode: If True, limits analysis for faster processing (default: True)
    """
    if analysis_type == "quick_summary":
        return await tool_get_quick_insights(time_period_in_days, CACHED_HISTORY)
    elif analysis_type == "basic":
        # For now, use comprehensive analysis with fast mode
        return await tool_get_browsing_insights(time_period_in_days, CACHED_HISTORY, fast_mode=True)
    elif analysis_type == "comprehensive":
        return await tool_get_browsing_insights(time_period_in_days, CACHED_HISTORY, fast_mode)
    else:
        raise ValueError(f"Unknown analysis_type: {analysis_type}. Use 'quick_summary', 'basic', or 'comprehensive'")

@mcp.tool()
async def search_browser_history(query: str) -> List[HistoryEntryDict]:
    """Search browser history for specific queries. Use this after getting history data.
    
    Args:
        query: Search term to look for in URLs and titles
    """
    return await tool_search_browser_history(query, CACHED_HISTORY)

@mcp.tool()
async def suggest_categories() -> Dict[str, Any]:
    """Get uncategorized URLs for custom categorization. Use this after running analysis.
    """
    return await tool_suggest_personalized_browser_categories(CACHED_HISTORY)

@mcp.tool()
def diagnose_safari_support() -> Dict[str, Any]:
    """Diagnose Safari support and accessibility. Useful for debugging Safari integration."""
    return check_safari_accessibility()

@mcp.tool()
def health_check() -> Dict[str, Any]:
    """Simple health check that returns immediately to test if the MCP server is working."""
    return {
        "status": "healthy",
        "message": "Browser MCP server is running",
        "timestamp": time.time()
    }

# Prompts
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

if __name__ == "__main__":
    mcp.run()
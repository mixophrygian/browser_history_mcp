import sqlite3
import os
import enum
from contextlib import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional
from mcp.server.fastmcp import FastMCP, Context

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("browser-storage-mcp")

FIREFOX_PROFILE_DIR = "/Users/eleanor.mazzarella/Library/Application Support/Firefox/Profiles/l42msng6.default-release"
PATH_TO_FIREFOX_HISTORY = os.path.join(FIREFOX_PROFILE_DIR, "places.sqlite")

# Chrome history path for macOS - need to verify this is correct
# CHROME_HISTORY_DIR = "/Users/eleanor.mazzarella/Library/Application Support/Google/Chrome/Default"
# PATH_TO_CHROME_HISTORY = os.path.join(CHROME_HISTORY_DIR, "History")

@dataclass(frozen=True)
class BrowserType(enum.Enum):
    FIREFOX = "firefox"
    #CHROME = "chrome"

@dataclass
class HistoryEntry:
    """Represents a single browser history entry"""
    url: str
    title: Optional[str]
    visit_count: int
    last_visit_time: datetime
    
    def to_dict(self) -> Dict:
        return {
            "url": self.url,
            "title": self.title,
            "visit_count": self.visit_count,
            "last_visit_time": self.last_visit_time.isoformat()
        }

@dataclass
class AppContext:
    firefox_db: sqlite3.Connection
    chrome_db: sqlite3.Connection

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with type-safe context"""
    firefox_db = None
    chrome_db = None
    
    try:
        # Initialize Firefox connection
        if os.path.exists(PATH_TO_FIREFOX_HISTORY):
            firefox_db = sqlite3.connect(PATH_TO_FIREFOX_HISTORY)
            logger.info("Connected to Firefox history database")
        else:
            logger.warning(f"Firefox history not found at {PATH_TO_FIREFOX_HISTORY}")
            
        # Initialize Chrome connection
        # if os.path.exists(PATH_TO_CHROME_HISTORY):
        #     chrome_db = sqlite3.connect(PATH_TO_CHROME_HISTORY)
        #     logger.info("Connected to Chrome history database")
        # else:
        #     logger.warning(f"Chrome history not found at {PATH_TO_CHROME_HISTORY}")
            
        yield AppContext(firefox_db=firefox_db, chrome_db=chrome_db)
        
    finally:
        if firefox_db:
            firefox_db.close()
        if chrome_db:
            chrome_db.close()

# Create server with lifespan
mcp = FastMCP(name="Browser History MCP", instructions="This server makes it possible to query a user's Firefox browser history, analyze it, and create a thoughtful report with an optional lense of productivity or learning.",  lifespan=app_lifespan)

@mcp.prompt()
def productivity_analysis() -> str:
    """Creates a comprehensive productivity analysis prompt"""
    return """
    Analyze the browser history to provide actionable productivity insights:
    
    1. **Time Distribution Analysis**
       - Calculate percentage of time on work-related vs entertainment sites
       - Identify peak productivity hours based on work-site visits
       - Show time spent per domain/category
    
    2. **Session Pattern Recognition**
       - Group visits into sessions (max 2-hour gaps between visits)
       - Identify "rabbit hole" sessions (many related searches in sequence)
       - Flag sessions that started productive but drifted
    
    3. **Focus Metrics**
       - Average session duration on productive sites
       - Number of context switches between work and entertainment
       - Longest uninterrupted work sessions
    
    4. **Actionable Recommendations**
       - Top 3 time-sink websites to consider blocking
       - Optimal work hours based on historical patterns
       - Specific habits to change (e.g., "You check Reddit 15x/day on average")
    
    Present findings in a clear format with specific numbers and time periods.
    """

@mcp.prompt()
def learning_analysis() -> str:
    """Creates a deep learning pattern analysis prompt"""
    return """
    Analyze browser history through the lens of learning effectiveness:
    
    1. **Learning Pattern Classification**
       - **Deep Learning**: Extended visits to documentation, tutorials, courses
       - **Quick Fixes**: Stack Overflow visits < 2 minutes, copy-paste solutions
       - **Research Sessions**: Multiple related sources in sequence
       - **Reference Checks**: Repeated visits to same documentation
    
    2. **Knowledge Building Analysis**
       - Identify learning trajectories (beginner → advanced topics)
       - Spot knowledge gaps (frequent searches for same concepts)
       - Track progression in specific technologies/topics
    
    3. **Learning Quality Metrics**
       - Average time on educational content
       - Depth score: ratio of documentation/tutorial time vs quick-answer sites
       - Learning velocity: new topics explored per week
    
    4. **Improvement Opportunities**
       - Topics frequently searched but never deeply studied
       - Suggest foundational resources for frequently accessed quick-fixes
       - Recommend structured learning paths based on scattered searches
    
    5. **Session Analysis**
       - Group by learning sessions (2-hour gap threshold)
       - Identify most productive learning times
       - Flag interrupted learning sessions
    
    Format as actionable insights with specific examples from the history.
    """

@mcp.prompt()
def privacy_audit() -> str:
    """Creates a privacy and security analysis prompt"""
    return """
    Analyze browser history for privacy and security concerns:
    
    1. **Sensitive Information Exposure**
       - Identify URLs containing personal information
       - Flag unencrypted (http://) site visits
       - Detect potential phishing domains
    
    2. **Digital Footprint Analysis**
       - Most frequently visited sites
       - Sites with account access (login pages)
       - Third-party tracker exposure estimate
    
    3. **Recommendations**
       - Sites that should use password manager
       - Candidates for private browsing
       - Services to consider replacing with privacy-focused alternatives
    """

@mcp.prompt()
def research_topic_extraction() -> str:
    """Extract and summarize research topics from browsing history"""
    return """
    Identify and summarize research topics from browsing patterns:
    
    1. **Topic Clustering**
       - Group related searches and visits into research topics
       - Identify primary research questions being explored
       - Track evolution of research focus over time
    
    2. **Research Depth Analysis**
       - Surface-level vs deep-dive research sessions
       - Number of sources consulted per topic
       - Time invested per research topic
    
    3. **Knowledge Synthesis**
       - Create brief summaries of main research findings per topic
       - Identify unanswered questions or incomplete research
       - Suggest next steps for each research thread
    
    Format as a research notebook with topics, key findings, and open questions.
    """

def _get_firefox_history(db: sqlite3.Connection, days: int) -> List[HistoryEntry]:
    """Get Firefox history from the last N days"""
    cursor = db.cursor()
    
    # Firefox stores timestamps as microseconds since Unix epoch
    cutoff_time = (datetime.now() - timedelta(days=days)).timestamp() * 1_000_000
    
    query = """
    SELECT DISTINCT h.url, h.title, h.visit_count, h.last_visit_date
    FROM moz_places h
    WHERE h.last_visit_date > ? 
    AND h.hidden = 0
    AND h.url NOT LIKE 'moz-extension://%'
    ORDER BY h.last_visit_date DESC
    """
    
    cursor.execute(query, (cutoff_time,))
    results = cursor.fetchall()
    
    entries = []
    for url, title, visit_count, last_visit_date in results:
        # Convert Firefox timestamp (microseconds) to datetime
        visit_time = datetime.fromtimestamp(last_visit_date / 1_000_000)
        
        entries.append(HistoryEntry(
            url=url or "",
            title=title,
            visit_count=visit_count or 0,
            last_visit_time=visit_time
        ))
    
    return entries

# def _get_chrome_history(db: sqlite3.Connection, days: int) -> List[HistoryEntry]:
#     """Get Chrome history from the last N days"""
#     cursor = db.cursor()
    
#     # Chrome stores timestamps as microseconds since Windows epoch (1601-01-01)
#     # Convert to Unix timestamp for comparison
#     windows_epoch_start = datetime(1601, 1, 1)
#     unix_epoch_start = datetime(1970, 1, 1)
#     epoch_diff = (unix_epoch_start - windows_epoch_start).total_seconds() * 1_000_000
    
#     cutoff_time = (datetime.now() - timedelta(days=days)).timestamp() * 1_000_000 + epoch_diff
    
#     query = """
#     SELECT DISTINCT u.url, u.title, u.visit_count, u.last_visit_time
#     FROM urls u
#     WHERE u.last_visit_time > ?
#     AND u.hidden = 0
#     ORDER BY u.last_visit_time DESC
#     """
    
#     cursor.execute(query, (cutoff_time,))
#     results = cursor.fetchall()
    
#     entries = []
#     for url, title, visit_count, last_visit_time in results:
#         # Convert Chrome timestamp to datetime
#         visit_time = datetime.fromtimestamp((last_visit_time - epoch_diff) / 1_000_000)
        
#         entries.append(HistoryEntry(
#             url=url or "",
#             title=title or "No Title", 
#             visit_count=visit_count or 0,
#             last_visit_time=visit_time
#         ))
    
#     return entries

@mcp.tool()
async def get_browser_history(context: AppContext, time_period_in_days: int, browser_type: BrowserType) -> List[Dict]:
    """Get browser history from Firefox for the specified time period in days"""
    
    if time_period_in_days <= 0:
        raise ValueError("time_period_in_days must be a positive integer")
    
    if browser_type == BrowserType.FIREFOX:
        if not context.firefox_db:
            raise RuntimeError("Firefox database not available")
        
        try:
            entries = _get_firefox_history(context.firefox_db, time_period_in_days)
            logger.info(f"Retrieved {len(entries)} Firefox history entries from last {time_period_in_days} days")
            return [entry.to_dict() for entry in entries]
        except sqlite3.Error as e:
            logger.error(f"Error querying Firefox history: {e}")
            raise RuntimeError(f"Failed to query Firefox history: {e}")
            
    # elif browser_type == BrowserType.CHROME:
    #     if not context.chrome_db:
    #         raise RuntimeError("Chrome database not available")
            
    #     try:
    #         entries = _get_chrome_history(context.chrome_db, time_period_in_days)
    #         logger.info(f"Retrieved {len(entries)} Chrome history entries from last {time_period_in_days} days")
    #         return [entry.to_dict() for entry in entries]
    #     except sqlite3.Error as e:
    #         logger.error(f"Error querying Chrome history: {e}")
    #         raise RuntimeError(f"Failed to query Chrome history: {e}")
    
    # else:
    #     raise ValueError(f"Unsupported browser type: {browser_type}")

@mcp.tool()
async def group_browsing_history_into_sessions(context: AppContext, history_data: List[Dict], max_gap_hours: float = 2.0) -> List[Dict]:
    """Group browser history into sessions based on time gaps"""
    
    if not history_data:
        return []
    
    # Sort by timestamp
    sorted_history = sorted(history_data, key=lambda x: x['last_visit_time'])
    
    sessions = []
    current_session = []
    
    for entry in sorted_history:
        visit_time = datetime.fromisoformat(entry['last_visit_time'])
        
        if not current_session:
            # Start first session
            current_session = [entry]
        else:
            # Check gap from last entry in current session
            last_time = datetime.fromisoformat(current_session[-1]['last_visit_time'])
            gap_hours = (visit_time - last_time).total_seconds() / 3600
            
            if gap_hours <= max_gap_hours:
                # Continue current session
                current_session.append(entry)
            else:
                # End current session and start new one
                sessions.append({
                    'session_start': current_session[0]['last_visit_time'],
                    'session_end': current_session[-1]['last_visit_time'],
                    'duration_minutes': (datetime.fromisoformat(current_session[-1]['last_visit_time']) - 
                                       datetime.fromisoformat(current_session[0]['last_visit_time'])).total_seconds() / 60,
                    'entry_count': len(current_session),
                    'entries': current_session
                })
                current_session = [entry]
    
    # Don't forget the last session
    if current_session:
        sessions.append({
            'session_start': current_session[0]['last_visit_time'],
            'session_end': current_session[-1]['last_visit_time'],
            'duration_minutes': (datetime.fromisoformat(current_session[-1]['last_visit_time']) - 
                               datetime.fromisoformat(current_session[0]['last_visit_time'])).total_seconds() / 60,
            'entry_count': len(current_session),
            'entries': current_session
        })
    
    logger.info(f"Grouped {len(history_data)} entries into {len(sessions)} sessions")
    return sessions

if __name__ == "__main__":
    mcp.run()
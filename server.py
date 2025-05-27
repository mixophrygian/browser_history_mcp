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
mcp = FastMCP("browser-history", lifespan=app_lifespan)

@mcp.prompt()
def productivity_analysis() -> str:
    """Creates a user prompt for analyzing productivity"""
    return """
    Focus on work vs. entertainment ratios, identify time sinks, suggest optimizations.
    Group history by "session", which can be inferred by the gap between timestamps.
    For example, a "session" might be a period of time with no more than 2 hours between visits.
    """

@mcp.prompt()
def learning_analysis() -> str:
    """Creates a user prompt for analyzing learning"""
    return """
    Analyze the browser history through the lens of learning and research. Try to infer when
    a url was visited in order to solve a specific problem versus when it was visited for general purpose understanding.
    If you think any URLs were visited in order for a "quick fix" or "quick answer", group this into a special section
    where there are opportunities for deeper understanding and more lasting learning.
    Group history by "session", which can be inferred by the gap between timestamps.
    For example, a "session" might be a period of time with no more than 2 hours between visits.
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
    """Get browser history from Firefox or Chrome for the specified time period"""
    
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
async def analyze_browsing_sessions(context: AppContext, history_data: List[Dict], max_gap_hours: float = 2.0) -> List[Dict]:
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
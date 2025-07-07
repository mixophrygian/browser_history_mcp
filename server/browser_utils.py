import os
import platform
from typing import Optional, List, Dict, Any, Union
import sqlite3
import glob
from datetime import datetime, timedelta
from general_utils import logger
from local_types import HistoryEntry, CachedHistory, ensure_history_entry_dict, HistoryEntryDict, BrowserHistoryResult


# FIREFOX

def get_firefox_profile_path() -> Optional[str]:
    """Automatically detect Firefox profile directory based on OS"""
    system = platform.system().lower()
    
    if system == "darwin":  # macOS
        base_path = os.path.expanduser("~/Library/Application Support/Firefox/Profiles")
    elif system == "linux":
        base_path = os.path.expanduser("~/.mozilla/firefox")
    elif system == "windows":
        base_path = os.path.join(os.getenv('APPDATA', ''), "Mozilla", "Firefox", "Profiles")
    else:
        logger.warning(f"Unsupported operating system: {system}")
        return None
    
    if not os.path.exists(base_path):
        logger.warning(f"Firefox profiles directory not found at: {base_path}")
        return None
    
    # Look for default profile directories
    profile_patterns = ["*.default-release", "*.default"]
    for pattern in profile_patterns:
        matches = glob.glob(os.path.join(base_path, pattern))
        if matches:
            # Return the first match (usually there's only one default profile)
            profile_path = matches[0]
            logger.info(f"Found Firefox profile: {profile_path}")
            return profile_path
    
    logger.warning(f"No default Firefox profile found in: {base_path}")
    return None

def get_firefox_history_path() -> Optional[str]:
    """Get the path to Firefox history database"""
    profile_path = get_firefox_profile_path()
    if not profile_path:
        return None
     
    history_path = os.path.join(profile_path, "places.sqlite")
    if os.path.exists(history_path):
        return history_path
    else:
        logger.warning(f"Firefox history database not found at: {history_path}")
        return None

def get_firefox_history(days: int) -> List[HistoryEntry]:
    """Get Firefox history from the last N days"""
        # Check if database exists
    if not os.path.exists(PATH_TO_FIREFOX_HISTORY):
        raise RuntimeError(f"Firefox history not found at {PATH_TO_FIREFOX_HISTORY}")
    
    # Connect to the database
    conn = sqlite3.connect(f"file:{PATH_TO_FIREFOX_HISTORY}?mode=ro", uri=True)
    try:
        cursor = conn.cursor()
        
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
    except Exception as e:
        logger.error(f"Error querying Firefox history: {e}")
        raise RuntimeError(f"Failed to query Firefox history: {e}")
    finally:
        if conn:
            conn.close()

# CHROME
def get_chrome_profile_path() -> Optional[str]:
    """Automatically detect Chrome profile directory based on OS"""
    system = platform.system().lower()
    
    if system == "darwin":  # macOS
        base_path = os.path.expanduser("~/Library/Application Support/Google/Chrome")
    elif system == "linux":
        base_path = os.path.expanduser("~/.config/google-chrome")
    elif system == "windows":
        base_path = os.path.join(os.getenv('LOCALAPPDATA', ''), "Google", "Chrome", "User Data")
    else:
        logger.warning(f"Unsupported operating system: {system}")
        return None
    
    if not os.path.exists(base_path):
        logger.warning(f"Chrome profiles directory not found at: {base_path}")
        return None
    
    # Chrome typically uses "Default" as the main profile directory
    profile_path = os.path.join(base_path, "Default")
    if os.path.exists(profile_path):
        logger.info(f"Found Chrome profile: {profile_path}")
        return profile_path
    
    logger.warning(f"Chrome Default profile not found in: {base_path}")
    return None

def get_chrome_history_path() -> Optional[str]:
    """Get the path to Chrome history database"""
    profile_path = get_chrome_profile_path()
    if not profile_path:
        return None
    
    history_path = os.path.join(profile_path, "History")
    if os.path.exists(history_path):
        return history_path
    else:
        logger.warning(f"Chrome history database not found at: {history_path}")
        return None


def get_chrome_history(days: int) -> List[HistoryEntry]:
    """Get Chrome history from the last N days"""
    if not os.path.exists(PATH_TO_CHROME_HISTORY):
        raise RuntimeError(f"Chrome history not found at {PATH_TO_CHROME_HISTORY}")
    
    # Connect to the database
    conn = sqlite3.connect(f"file:{PATH_TO_CHROME_HISTORY}?mode=ro", uri=True)

    try: 
        cursor = conn.cursor()
    
        # Chrome stores timestamps as microseconds since Windows epoch (1601-01-01)
        # Convert to Unix timestamp for comparison
        windows_epoch_start = datetime(1601, 1, 1)
        unix_epoch_start = datetime(1970, 1, 1)
        epoch_diff = (unix_epoch_start - windows_epoch_start).total_seconds() * 1_000_000
    
        cutoff_time = (datetime.now() - timedelta(days=days)).timestamp() * 1_000_000 + epoch_diff
        
        query = """
        SELECT DISTINCT u.url, u.title, u.visit_count, u.last_visit_time
        FROM urls u
        WHERE u.last_visit_time > ?
        AND u.hidden = 0
        ORDER BY u.last_visit_time DESC
        """
        
        cursor.execute(query, (cutoff_time,))
        results = cursor.fetchall()
        
        entries = []
        for url, title, visit_count, last_visit_time in results:
            # Convert Chrome timestamp to datetime
            visit_time = datetime.fromtimestamp((last_visit_time - epoch_diff) / 1_000_000)
            
            entries.append(HistoryEntry(
                url=url or "",
                title=title or "No Title", 
                visit_count=visit_count or 0,
                last_visit_time=visit_time
            ))
        
        return entries
    except Exception as e:
        logger.error(f"Error querying Chrome history: {e}")
        raise RuntimeError(f"Failed to query Chrome history: {e}")
    finally:
        if conn:
            conn.close()

# SAFARI

def get_safari_profile_path() -> Optional[str]:
    """Automatically detect Safari profile directory based on OS"""
    system = platform.system().lower()
    
    if system == "darwin":  # macOS
        # Safari stores its data in the WebKit directory
        base_path = os.path.expanduser("~/Library/WebKit/com.apple.Safari")
        
        # Also check the traditional Safari location as fallback
        if not os.path.exists(base_path):
            base_path = os.path.expanduser("~/Library/Safari")
    else:
        logger.warning(f"Safari is only supported on macOS, not {system}")
        return None
    
    if not os.path.exists(base_path):
        logger.warning(f"Safari profiles directory not found at: {base_path}")
        return None
    
    logger.info(f"Found Safari profile: {base_path}")
    return base_path

def get_safari_history_path() -> Optional[str]:
    """Get the path to Safari history database"""
    profile_path = get_safari_profile_path()
    if not profile_path:
        return None
    
    # Modern Safari (macOS 10.15+) uses different storage mechanisms
    # Try different possible Safari database locations and names
    possible_paths = [
        # Traditional locations (older Safari versions)
        os.path.join(profile_path, "History.db"),
        os.path.join(profile_path, "WebpageIcons.db"),
        os.path.join(profile_path, "Databases.db"),
        
        # Modern WebKit locations
        os.path.join(profile_path, "WebsiteData", "LocalStorage"),
        os.path.join(profile_path, "WebsiteData", "IndexedDB"),
        os.path.join(profile_path, "WebsiteData", "ResourceLoadStatistics"),
        
        # Alternative locations for modern Safari
        os.path.join(os.path.expanduser("~/Library/Safari"), "History.db"),
        os.path.join(os.path.expanduser("~/Library/Safari"), "WebpageIcons.db"),
        
        # CloudKit-related locations
        os.path.join(os.path.expanduser("~/Library/Application Support/CloudDocs/session/containers/iCloud.com.apple.Safari"), "Documents"),
    ]
    
    for history_path in possible_paths:
        if os.path.exists(history_path):
            logger.info(f"Found Safari database at: {history_path}")
            return history_path
    
    logger.warning(f"No Safari history database found in: {profile_path}")
    logger.warning("Modern Safari (macOS 10.15+) uses CloudKit for history syncing and has limited programmatic access")
    return None

def get_safari_history(days: int) -> List[HistoryEntry]:
    """Get Safari history from the last N days"""
    if not os.path.exists(PATH_TO_SAFARI_HISTORY):
        raise RuntimeError(f"Safari history not found at {PATH_TO_SAFARI_HISTORY}")
    
    # Connect to the database
    try:
        conn = sqlite3.connect(f"file:{PATH_TO_SAFARI_HISTORY}?mode=ro", uri=True)
    except sqlite3.OperationalError as e:
        if "unable to open database file" in str(e).lower():
            raise RuntimeError(
                f"Cannot access Safari database: {e}. "
                "Modern Safari (macOS 10.15+) uses CloudKit for history syncing and has limited programmatic access. "
                "Consider using Firefox or Chrome for browser history analysis, or export Safari history manually through Safari's interface."
            )
        else:
            raise RuntimeError(f"Failed to connect to Safari database: {e}")
    
    try: 
        cursor = conn.cursor()
        
        # First, let's see what tables are available
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"Available tables in Safari database: {tables}")
        
        # Safari stores timestamps as seconds since Unix epoch
        cutoff_time = (datetime.now() - timedelta(days=days)).timestamp()
        
        # Try different possible Safari database structures
        query = None
        
        # Check if we have the traditional history tables
        if 'history_items' in tables and 'history_visits' in tables:
            query = """
            SELECT DISTINCT hi.url, hi.title, COUNT(hv.id) as visit_count, MAX(hv.visit_time) as last_visit_time
            FROM history_items hi
            JOIN history_visits hv ON hi.id = hv.history_item
            WHERE hv.visit_time > ?
            GROUP BY hi.id, hi.url, hi.title
            ORDER BY last_visit_time DESC
            """
        elif 'urls' in tables:
            # Fallback to Chrome-like structure
            query = """
            SELECT DISTINCT u.url, u.title, u.visit_count, u.last_visit_time
            FROM urls u
            WHERE u.last_visit_time > ?
            ORDER BY u.last_visit_time DESC
            """
        elif 'moz_places' in tables:
            # Fallback to Firefox-like structure
            query = """
            SELECT DISTINCT h.url, h.title, h.visit_count, h.last_visit_date
            FROM moz_places h
            WHERE h.last_visit_date > ? 
            AND h.hidden = 0
            ORDER BY h.last_visit_date DESC
            """
        
        if query is None:
            raise RuntimeError(
                f"Safari database structure not recognized. Available tables: {tables}. "
                "Modern Safari uses CloudKit for history syncing and has limited programmatic access. "
                "Consider using Firefox or Chrome for browser history analysis."
            )
        
        cursor.execute(query, (cutoff_time,))
        results = cursor.fetchall()
        
        entries = []
        for url, title, visit_count, last_visit_time in results:
            # Convert Safari timestamp (seconds) to datetime
            visit_time = datetime.fromtimestamp(last_visit_time)
            
            entries.append(HistoryEntry(
                url=url or "",
                title=title or "No Title", 
                visit_count=visit_count or 0,
                last_visit_time=visit_time
            ))
        
        return entries
    except Exception as e:
        logger.error(f"Error querying Safari history: {e}")
        if "no such table" in str(e).lower():
            raise RuntimeError(
                f"Safari database structure not supported: {e}. "
                "Modern Safari uses CloudKit for history syncing and has limited programmatic access. "
                "Consider using Firefox or Chrome for browser history analysis."
            )
        else:
            raise RuntimeError(f"Failed to query Safari history: {e}")
    finally:
        if conn:
            conn.close()

def check_safari_accessibility() -> Dict[str, Any]:
    """Check Safari accessibility and provide diagnostics"""
    result = {
        "safari_installed": os.path.exists("/Applications/Safari.app"),
        "profile_path": get_safari_profile_path(),
        "history_path": PATH_TO_SAFARI_HISTORY,
        "accessible": False,
        "error": None,
        "limitations": "Modern Safari (macOS 10.15+) uses CloudKit for history syncing and has limited programmatic access"
    }
    
    if not result["safari_installed"]:
        result["error"] = "Safari is not installed"
        return result
    
    if not result["history_path"]:
        result["error"] = "Safari history database not found"
        result["recommendation"] = "Consider using Firefox or Chrome for browser history analysis, or export Safari history manually through Safari's interface"
        return result
    
    try:
        # Try to connect to the database
        conn = sqlite3.connect(f"file:{result['history_path']}?mode=ro", uri=True)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        result["accessible"] = True
        result["tables"] = tables
        result["message"] = f"Safari database accessible with {len(tables)} tables"
        result["note"] = "This may be limited data - modern Safari uses CloudKit for full history syncing"
    except Exception as e:
        result["error"] = str(e)
        result["message"] = "Safari database not accessible"
        result["recommendation"] = "Modern Safari has limited programmatic access. Consider using Firefox or Chrome for browser history analysis"
    
    return result
# UTILS

def tool_detect_available_browsers() -> Dict[str, Any]:
    browsers_to_check = []
    
    # Check Firefox
    if PATH_TO_FIREFOX_HISTORY:
        browsers_to_check.append(('firefox', PATH_TO_FIREFOX_HISTORY))
    
    # Check Chrome
    if PATH_TO_CHROME_HISTORY:
        browsers_to_check.append(('chrome', PATH_TO_CHROME_HISTORY))
    
    # Check Safari
    if PATH_TO_SAFARI_HISTORY:
        browsers_to_check.append(('safari', PATH_TO_SAFARI_HISTORY))
    
    if not browsers_to_check:
        logger.warning("No browser history databases found")
        return None
    
    browsers_in_use = []
    for browser_name, db_path in browsers_to_check:
        logger.info(f"Checking {browser_name} database at {db_path}")
        try:
            # Try to connect with read-only mode
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            
            # Test if we can actually query the database
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table';")
            table_count = cursor.fetchone()[0]
            conn.close()
            
            logger.info(f"Successfully connected to {browser_name} database and queried {table_count} tables. Browser may still be running, encourage the user to close this browser to make history available.")
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e).lower():
                logger.info(f"Database locked for {browser_name} - browser is likely open and active - prompt the user to close it to get complete history.")
                browsers_in_use.append(browser_name)
            else:
                logger.warning(f"Error connecting to {browser_name} database: {e} - please inform the user that this browser is not available for analysis.")
        except Exception as e:
            logger.warning(f"Unexpected error connecting to {browser_name} database: {e}")
            browsers_in_use.append(browser_name)
    
    # If no browser is locked, return all available browsers
    if not browsers_in_use and browsers_to_check:
        available_browsers = [browser[0] for browser in browsers_to_check]
        logger.info(f"No active browser detected, available browsers: {available_browsers}")
        return {
            "available_browsers": available_browsers,
            "active_browsers": [],
            "recommended_action": "Please close all browsers to analyze history. You can restore tabs with Ctrl+Shift+T"
        }
    
    return {
        "available_browsers": [browser[0] for browser in browsers_to_check],
        "active_browsers": browsers_in_use,  # Currently running
        "recommended_action": "Please close the browser to analyze its history. You can restore tabs with Ctrl+Shift+T"
    }

PATH_TO_FIREFOX_HISTORY = get_firefox_history_path()
PATH_TO_CHROME_HISTORY = get_chrome_history_path()
PATH_TO_SAFARI_HISTORY = get_safari_history_path()

async def tool_get_browser_history(time_period_in_days: int, CACHED_HISTORY: CachedHistory, browser_type: Optional[str] = None, all_browsers: bool = True) -> Union[List[HistoryEntryDict], BrowserHistoryResult]:

    if time_period_in_days <= 0:
        raise ValueError("time_period_in_days must be a positive integer")
    
    # Map browser types to their handler functions
    browser_handlers = {
        "firefox": get_firefox_history,
        "chrome": get_chrome_history,
        "safari": get_safari_history
    }
    
    if all_browsers:
        # Get history from all available browsers
        all_entries = []
        successful_browsers = []
        failed_browsers = []
        failure_reasons = {}
        
        browser_status = tool_detect_available_browsers()
        
        if not browser_status:
            raise RuntimeError("No browser history databases found. Please ensure Firefox, Chrome, or Safari is installed and try again.")
        
        available_browsers = browser_status.get('available_browsers', [])
        if not available_browsers:
            raise RuntimeError("No browser history databases found. Please ensure Firefox, Chrome, or Safari is installed and try again.")
        
        for browser in available_browsers:
            try:
                entries = browser_handlers[browser](time_period_in_days)
                logger.info(f"Retrieved {len(entries)} {browser} history entries from last {time_period_in_days} days")
                all_entries.extend([entry.to_dict() for entry in entries])
                successful_browsers.append(browser)
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"Failed to get {browser} history: {error_msg}. If the database is locked, please try closing the browser and running the tool again.")
                failed_browsers.append(browser)
                failure_reasons[browser] = error_msg
                continue
        
        # If we have any successful browsers, return partial results
        if successful_browsers:
            recommendation = ""
            if failed_browsers:
                locked_browsers = [browser for browser in failed_browsers if "database is locked" in failure_reasons.get(browser, "").lower()]
                if locked_browsers:
                    recommendation = f"Some browsers ({', '.join(locked_browsers)}) are currently open and their databases are locked. Close these browsers and retry to get complete history. "
                recommendation += f"Successfully retrieved {len(all_entries)} entries from {', '.join(successful_browsers)}."
            else:
                recommendation = f"Successfully retrieved {len(all_entries)} entries from all browsers."
            
            logger.info(f"Retrieved total of {len(all_entries)} history entries from {len(successful_browsers)} browsers")
            
            return {
                "history_entries": all_entries,
                "successful_browsers": successful_browsers,
                "failed_browsers": failed_browsers,
                "failure_reasons": failure_reasons,
                "total_entries": len(all_entries),
                "recommendation": recommendation
            }
        
        # If no browsers succeeded, raise error with detailed information
        error_details = "; ".join([f"{browser}: {reason}" for browser, reason in failure_reasons.items()])
        raise RuntimeError(f"Failed to retrieve history from any browser: {error_details}. Try closing browsers - history is locked while browsers are running.")
    
    else:
        # Single browser mode (original behavior)
        if browser_type is None:
            browser_status = tool_detect_available_browsers()
            if browser_status is None:
                raise RuntimeError("This MCP currently only supports Firefox, Chrome, and Safari. Please ensure one of these browsers is installed and try again.")
            
            # Get the first available browser from the available_browsers list
            available_browsers = browser_status.get('available_browsers', [])
            browser_type = available_browsers[0] if available_browsers else None
                
            if browser_type is None:
                raise RuntimeError("No browser history databases found. Please ensure Firefox, Chrome, or Safari is installed and try again.")
                
            logger.info(f"Auto-detected active browser: {browser_type}")
        
        if browser_type not in browser_handlers:
            raise ValueError(f"Unsupported browser type: {browser_type}. Supported types: {list(browser_handlers.keys())}")
        
        try:
            entries = browser_handlers[browser_type](time_period_in_days)
            logger.info(f"Retrieved {len(entries)} {browser_type} history entries from last {time_period_in_days} days")

            # Ensure we are always working with dictionaries
            entries_dict = [ensure_history_entry_dict(e) for e in entries]

            # Cache the history for later use
            CACHED_HISTORY.add_history(entries_dict, time_period_in_days, browser_type)

            return entries_dict
        except sqlite3.Error as e:
            logger.error(f"Error querying {browser_type} history: {e}")
            raise RuntimeError(f"Failed to query {browser_type} history: {e}. Try closing the browser - history is locked while the browser is running.")
        except Exception as e:
            logger.error(f"Unexpected error querying {browser_type} history: {e}")
            raise RuntimeError(f"Failed to query {browser_type} history: {e}")

async def tool_search_browser_history(query: str, CACHED_HISTORY: CachedHistory) -> List[HistoryEntryDict]:
    if not CACHED_HISTORY.has_history():
        history_result = await tool_get_browser_history(7, CACHED_HISTORY, "", True)
        # Handle the new return type
        if isinstance(history_result, dict) and "history_entries" in history_result:
            history = history_result["history_entries"]
        else:
            history = history_result  # Fallback for single browser mode
    else:
        history = CACHED_HISTORY.get_history()
    
    query_lower = query.lower()
    results = []
    
    for entry in history:
        url = entry.get('url', '')
        title = entry.get('title', '')
        
        # Handle None values safely
        if (isinstance(url, str) and query_lower in url.lower()) or \
           (isinstance(title, str) and query_lower in title.lower()):
            results.append(entry)
    
    return results

def tool_test_browser_access() -> Dict[str, Any]:
    """Quick test to see what's accessible"""
    return {
        "firefox": PATH_TO_FIREFOX_HISTORY is not None,
        "chrome": PATH_TO_CHROME_HISTORY is not None,
        "safari": PATH_TO_SAFARI_HISTORY is not None,
        "message": "Run detect_active_browser for detailed status"
    }
import os
import platform
from typing import Optional, List
import sqlite3
from datetime import datetime, timedelta
from general_utils import logger
from local_types import HistoryEntry


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

PATH_TO_FIREFOX_HISTORY = get_firefox_history_path()
PATH_TO_CHROME_HISTORY = get_chrome_history_path()
PATH_TO_SAFARI_HISTORY = get_safari_history_path()

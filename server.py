import sqlite3
import os
import platform
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Any
from mcp.server.fastmcp import FastMCP
from urllib.parse import urlparse
from collections import Counter, defaultdict
import re
from functools import lru_cache
import glob

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("browser-storage-mcp")

BROWSING_CATEGORIES = { # update this to include sites you want to track
    'social_media': {
        'domains': [
            'facebook.com', 'twitter.com', 'x.com', 'instagram.com', 'reddit.com', 
            'linkedin.com', 'tiktok.com', 'snapchat.com', 'pinterest.com', 
            'tumblr.com', 'discord.com', 'slack.com', 'whatsapp.com', 'telegram.org',
            'mastodon.social', 'threads.net', 'bsky.social', 'bereal.com'
        ],
        'patterns': [r'social', r'/comments/', r'/status/', r'/post/'],
        'subcategories': {
            'professional': ['linkedin.com', 'slack.com'],
            'messaging': ['whatsapp.com', 'telegram.org', 'discord.com'],
            'content_sharing': ['instagram.com', 'tiktok.com', 'pinterest.com']
        }
    },
    
    'entertainment': {
        'domains': [
            'youtube.com', 'netflix.com', 'spotify.com', 'twitch.tv', 'hulu.com',
            'disneyplus.com', 'hbomax.com', 'primevideo.com', 'vimeo.com',
            'soundcloud.com', 'pandora.com', 'applemusic.com', 'deezer.com',
            'crunchyroll.com', 'funimation.com', 'steam.com', 'epicgames.com',
            'ign.com', 'gamespot.com', 'kotaku.com', 'polygon.com'
        ],
        'patterns': [r'/watch', r'/video/', r'/episode/', r'/game/', r'wiki\.fandom\.com'],
        'subcategories': {
            'video': ['youtube.com', 'netflix.com', 'twitch.tv'],
            'music': ['spotify.com', 'soundcloud.com', 'pandora.com'],
            'gaming': ['steam.com', 'epicgames.com', 'ign.com', r'\.fandom\.com']
        }
    },
    
    'development': {
        'domains': [
            'stackoverflow.com', 'github.com', 'gitlab.com', 'bitbucket.org',
            'developer.mozilla.org', 'w3schools.com', 'css-tricks.com',
            'dev.to', 'hashnode.dev', 'codesandbox.io', 'codepen.io',
            'jsfiddle.net', 'replit.com', 'vercel.com', 'netlify.com',
            'npmjs.com', 'pypi.org', 'crates.io', 'packagist.org',
            'docker.com', 'kubernetes.io', 'terraform.io'
        ],
        'patterns': [
            r'docs\..*\.(?:com|org|io)', r'.*\.readthedocs\.io', r'/documentation/',
            r'/api/', r'/reference/', r'github\.com/.*/(?:issues|pull|wiki)',
            r'stackoverflow\.com/questions/'
        ],
        'subcategories': {
            'q&a': ['stackoverflow.com', 'dev.to'],
            'repositories': ['github.com', 'gitlab.com', 'bitbucket.org'],
            'documentation': [r'docs\.', r'\.readthedocs\.io', 'developer.mozilla.org'],
            'tools': ['codesandbox.io', 'codepen.io', 'replit.com']
        }
    },
    
    'learning': {
        'domains': [
            'coursera.org', 'udemy.com', 'edx.org', 'khanacademy.org',
            'udacity.com', 'pluralsight.com', 'lynda.com', 'skillshare.com',
            'masterclass.com', 'brilliant.org', 'datacamp.com', 'codecademy.com',
            'freecodecamp.org', 'mit.edu', 'stanford.edu', 'harvard.edu',
            'arxiv.org', 'scholar.google.com', 'jstor.org', 'pubmed.ncbi.nlm.nih.gov',
            'wikipedia.org', 'wikihow.com', 'instructables.com'
        ],
        'patterns': [
            r'/course/', r'/tutorial/', r'/learn/', r'/guide/', r'/how-to',
            r'\.edu/', r'/research/', r'/paper/', r'/study/'
        ],
        'subcategories': {
            'moocs': ['coursera.org', 'udemy.com', 'edx.org'],
            'technical': ['freecodecamp.org', 'codecademy.com', 'datacamp.com'],
            'academic': ['arxiv.org', 'scholar.google.com', 'jstor.org', r'\.edu/'],
            'practical': ['wikihow.com', 'instructables.com']
        }
    },
    
    'productivity': {
        'domains': [
            'notion.so', 'trello.com', 'asana.com', 'todoist.com', 'monday.com',
            'clickup.com', 'airtable.com', 'basecamp.com', 'jira.atlassian.com',
            'confluence.atlassian.com', 'evernote.com', 'onenote.com', 'obsidian.md',
            'roamresearch.com', 'workflowy.com', 'calendar.google.com', 'outlook.com',
            'zoom.us', 'meet.google.com', 'teams.microsoft.com', 'calendly.com'
        ],
        'patterns': [r'/calendar/', r'/tasks/', r'/projects/', r'/workspace/'],
        'subcategories': {
            'project_management': ['trello.com', 'asana.com', 'jira.atlassian.com'],
            'notes': ['notion.so', 'evernote.com', 'obsidian.md'],
            'communication': ['zoom.us', 'meet.google.com', 'teams.microsoft.com']
        }
    },
    
    'news': {
        'domains': [
            'nytimes.com', 'washingtonpost.com', 'wsj.com', 'ft.com', 'economist.com',
            'bbc.com', 'cnn.com', 'reuters.com', 'apnews.com', 'npr.org',
            'theguardian.com', 'foxnews.com', 'nbcnews.com', 'abcnews.go.com',
            'usatoday.com', 'politico.com', 'axios.com', 'bloomberg.com',
            'techcrunch.com', 'theverge.com', 'arstechnica.com', 'wired.com',
            'hackernews.com', 'news.ycombinator.com', 'lobste.rs', 'slashdot.org'
        ],
        'patterns': [r'/article/', r'/story/', r'/news/', r'/\d{4}/\d{2}/\d{2}/'],
        'subcategories': {
            'mainstream': ['nytimes.com', 'bbc.com', 'cnn.com'],
            'tech': ['techcrunch.com', 'theverge.com', 'arstechnica.com'],
            'aggregators': ['news.ycombinator.com', 'reddit.com/r/news']
        }
    },
    
    'shopping': {
        'domains': [
            'amazon.com', 'ebay.com', 'etsy.com', 'alibaba.com', 'walmart.com',
            'target.com', 'bestbuy.com', 'homedepot.com', 'lowes.com', 'ikea.com',
            'wayfair.com', 'shopify.com', 'wish.com', 'costco.com', 'sephora.com',
            'ulta.com', 'nike.com', 'adidas.com', 'apple.com', 'samsung.com'
        ],
        'patterns': [r'/product/', r'/cart/', r'/checkout/', r'/shop/', r'/store/'],
        'subcategories': {
            'marketplace': ['amazon.com', 'ebay.com', 'etsy.com'],
            'retail': ['walmart.com', 'target.com', 'costco.com'],
            'specialty': ['sephora.com', 'nike.com', 'apple.com']
        }
    },
    
    'finance': {
        'domains': [
            'chase.com', 'bankofamerica.com', 'wellsfargo.com', 'citi.com',
            'paypal.com', 'venmo.com', 'cashapp.com', 'zelle.com', 'wise.com',
            'coinbase.com', 'binance.com', 'kraken.com', 'robinhood.com',
            'etrade.com', 'fidelity.com', 'vanguard.com', 'schwab.com',
            'mint.com', 'ynab.com', 'personalcapital.com', 'creditkarma.com'
        ],
        'patterns': [r'/banking/', r'/wallet/', r'/account/', r'/trading/'],
        'subcategories': {
            'banking': ['chase.com', 'bankofamerica.com', 'wellsfargo.com'],
            'payments': ['paypal.com', 'venmo.com', 'cashapp.com'],
            'investing': ['robinhood.com', 'fidelity.com', 'vanguard.com'],
            'crypto': ['coinbase.com', 'binance.com', 'kraken.com']
        }
    },
    
    'health': {
        'domains': [
            'webmd.com', 'mayoclinic.org', 'healthline.com', 'medlineplus.gov',
            'nih.gov', 'cdc.gov', 'who.int', 'drugs.com', 'rxlist.com',
            'myfitnesspal.com', 'fitbit.com', 'strava.com', 'headspace.com',
            'calm.com', 'betterhelp.com', 'talkspace.com', 'zocdoc.com'
        ],
        'patterns': [r'/health/', r'/medical/', r'/symptoms/', r'/conditions/'],
        'subcategories': {
            'medical_info': ['webmd.com', 'mayoclinic.org', 'healthline.com'],
            'fitness': ['myfitnesspal.com', 'fitbit.com', 'strava.com'],
            'mental_health': ['headspace.com', 'calm.com', 'betterhelp.com']
        }
    },
    
    'reference': {
        'domains': [
            'google.com', 'bing.com', 'duckduckgo.com', 'yandex.com', 'baidu.com',
            'dictionary.com', 'thesaurus.com', 'merriam-webster.com', 'oxforddictionaries.com',
            'translate.google.com', 'deepl.com', 'wolframalpha.com', 'archive.org',
            'maps.google.com', 'openstreetmap.org', 'waze.com', 'weather.com',
            'timeanddate.com', 'xe.com', 'calculator.net'
        ],
        'patterns': [r'/search', r'/define/', r'/translate/', r'/maps/', r'/directions/'],
        'subcategories': {
            'search': ['google.com', 'bing.com', 'duckduckgo.com'],
            'language': ['dictionary.com', 'translate.google.com', 'deepl.com'],
            'utilities': ['maps.google.com', 'weather.com', 'xe.com']
        }
    },
    
    'professional': {
        'domains': [
            'salesforce.com', 'hubspot.com', 'zendesk.com', 'intercom.com',
            'mailchimp.com', 'constantcontact.com', 'hootsuite.com', 'buffer.com',
            'canva.com', 'figma.com', 'adobe.com', 'sketch.com', 'miro.com',
            'tableau.com', 'powerbi.microsoft.com', 'datastudio.google.com'
        ],
        'patterns': [r'/dashboard/', r'/analytics/', r'/reports/', r'/design/'],
        'subcategories': {
            'crm': ['salesforce.com', 'hubspot.com', 'zendesk.com'],
            'marketing': ['mailchimp.com', 'hootsuite.com', 'buffer.com'],
            'design': ['canva.com', 'figma.com', 'adobe.com'],
            'analytics': ['tableau.com', 'powerbi.microsoft.com']
        }
    }
}

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


PATH_TO_FIREFOX_HISTORY = get_firefox_history_path()
PATH_TO_CHROME_HISTORY = get_chrome_history_path()
PATH_TO_SAFARI_HISTORY = get_safari_history_path()

@dataclass(frozen=True)
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
    firefox_db: Optional[sqlite3.Connection]
    chrome_db: Optional[sqlite3.Connection]
    safari_db: Optional[sqlite3.Connection]

mcp = FastMCP(name="Browser History MCP", instructions="This server makes it possible to query a user's Firefox, Chrome, or Safari browser history, analyze it, and create a thoughtful report with an optional lense of productivity or learning.")

@mcp.prompt()
def productivity_analysis() -> str:
    """Creates a comprehensive productivity analysis prompt"""
    return """
    Analyze the browser history to provide actionable productivity insights.

    The MCP tool @get_browsing_insights will be used to get the browser history and insights.
        
    Then provide:
    
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

def _get_firefox_history(days: int) -> List[HistoryEntry]:
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

def _get_chrome_history(days: int) -> List[HistoryEntry]:
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

def _get_safari_history(days: int) -> List[HistoryEntry]:
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
        try:
            # Try to connect with read-only mode
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            conn.close()
            logger.info(f"Successfully connected to {browser_name} database - browser is likely closed")
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e).lower():
                logger.info(f"Database locked for {browser_name} - browser is likely open and active")
                browsers_in_use.append(browser_name)
            else:
                logger.warning(f"Error connecting to {browser_name} database: {e}")
        except Exception as e:
            logger.warning(f"Unexpected error connecting to {browser_name} database: {e}")
    
    # If no browser is locked, return all available browsers
    if not browsers_in_use and browsers_to_check:
        available_browsers = [browser[0] for browser in browsers_to_check]
        logger.info(f"No active browser detected, available browsers: {available_browsers}")
        return available_browsers
    
    return {
        "available_browsers": [browser[0] for browser in browsers_to_check],
        "active_browsers": browsers_in_use,  # Currently running
        "recommended_action": "Please close the browser to analyze its history. You can restore tabs with Ctrl+Shift+T"
    }


async def get_browser_history(time_period_in_days: int, browser_type: Optional[str] = None, all_browsers: bool = False) -> List[Dict]:
    """Get browser history from the specified browser(s) for the given time period.
    
    Args:
        time_period_in_days: Number of days of history to retrieve
        browser_type: Browser type ('firefox', 'chrome', 'safari', or None for auto-detect)
        all_browsers: If True, get history from all available browsers. If False, use browser_type or auto-detect.
    """
    
    if time_period_in_days <= 0:
        raise ValueError("time_period_in_days must be a positive integer")
    
    # Map browser types to their handler functions
    browser_handlers = {
        "firefox": _get_firefox_history,
        "chrome": _get_chrome_history,
        "safari": _get_safari_history
    }
    
    if all_browsers:
        # Get history from all available browsers
        all_entries = []
        available_browsers = detect_active_browser()
        
        if not available_browsers:
            raise RuntimeError("No browser history databases found. Please ensure Firefox, Chrome, or Safari is installed and try again.")
        
        for browser in available_browsers:
            try:
                entries = browser_handlers[browser](time_period_in_days)
                logger.info(f"Retrieved {len(entries)} {browser} history entries from last {time_period_in_days} days")
                all_entries.extend([entry.to_dict() for entry in entries])
            except Exception as e:
                logger.warning(f"Failed to get {browser} history: {e}")
                continue
        
        if not all_entries:
            raise RuntimeError("Failed to retrieve history from any browser. Try closing browsers - history is locked while browsers are running.")
        
        logger.info(f"Retrieved total of {len(all_entries)} history entries from all browsers")
        return all_entries
    
    else:
        # Single browser mode (original behavior)
        if browser_type is None:
            detected_browsers = detect_active_browser()
            if detected_browsers is None:
                raise RuntimeError("This MCP currently only supports Firefox, Chrome, and Safari. Please ensure one of these browsers is installed and try again.")
            
            # If detect_active_browser returns a list, take the first available browser
            if isinstance(detected_browsers, list):
                browser_type = detected_browsers[0] if detected_browsers else None
            else:
                browser_type = detected_browsers
                
            if browser_type is None:
                raise RuntimeError("No browser history databases found. Please ensure Firefox, Chrome, or Safari is installed and try again.")
                
            logger.info(f"Auto-detected active browser: {browser_type}")
        
        if browser_type not in browser_handlers:
            raise ValueError(f"Unsupported browser type: {browser_type}. Supported types: {list(browser_handlers.keys())}")
        
        try:
            entries = browser_handlers[browser_type](time_period_in_days)
            logger.info(f"Retrieved {len(entries)} {browser_type} history entries from last {time_period_in_days} days")
            return [entry.to_dict() for entry in entries]
        except sqlite3.Error as e:
            logger.error(f"Error querying {browser_type} history: {e}")
            raise RuntimeError(f"Failed to query {browser_type} history: {e}. Try closing the browser - history is locked while the browser is running.")
        except Exception as e:
            logger.error(f"Unexpected error querying {browser_type} history: {e}")
            raise RuntimeError(f"Failed to query {browser_type} history: {e}")

async def categorize_browsing_history(history_data: List[Dict]) -> Dict[str, Dict]:
    """Categorize URLs into meaningful groups with patterns and subcategories.
    
    Args:
        history_data: List of history entries from get_browser_history
    """
    
    categorized = defaultdict(lambda: {
        'entries': [],
        'subcategories': defaultdict(list),
        'count': 0,
        'unique_domains': set(),
        'total_visits': 0
    })
    
    uncategorized = []
    
    for entry in history_data:
        url = entry['url'].lower()
        domain = urlparse(url).netloc.lower()
        categorized_flag = False
        
        for category, config in BROWSING_CATEGORIES.items():
            # Check domain matches
            if any(d in domain for d in config['domains']):
                categorized_flag = True
                _add_to_category(categorized[category], entry, domain, config)
                break
            
            # Check pattern matches
            if 'patterns' in config:
                for pattern in config['patterns']:
                    if re.search(pattern, url):
                        categorized_flag = True
                        _add_to_category(categorized[category], entry, domain, config)
                        break
                if categorized_flag:
                    break
        
        if not categorized_flag:
            uncategorized.append(entry)
    
    # Add uncategorized
    if uncategorized:
        categorized['other'] = {
            'entries': uncategorized,
            'count': len(uncategorized),
            'unique_domains': set(urlparse(e['url']).netloc for e in uncategorized),
            'total_visits': sum(e.get('visit_count', 1) for e in uncategorized)
        }
    
    return dict(categorized)

def _add_to_category(category_data, entry, domain, config):
    """Helper to add entry to category with subcategory detection."""
    category_data['entries'].append(entry)
    category_data['count'] += 1
    category_data['unique_domains'].add(domain)
    category_data['total_visits'] += entry.get('visit_count', 1)
    
    # Determine subcategory
    if 'subcategories' in config:
        for subcat, patterns in config['subcategories'].items():
            if any(p in domain for p in patterns if isinstance(p, str)):
                category_data['subcategories'][subcat].append(entry)
                break

async def analyze_domain_frequency(history_data: List[Dict], top_n: int = 20) -> List[Dict]:
    """Analyze most frequently visited domains.
    
    Args:
        history_data: List of history entries from get_browser_history
        top_n: Number of top domains to return
    """
    
    domain_stats = defaultdict(lambda: {'count': 0, 'total_visits': 0, 'titles': set()})
    
    for entry in history_data:
        domain = urlparse(entry['url']).netloc
        if domain:
            domain_stats[domain]['count'] += 1
            domain_stats[domain]['total_visits'] += entry.get('visit_count', 1)
            if entry.get('title'):
                domain_stats[domain]['titles'].add(entry['title'])
    
    # Convert to list and sort by visit count
    domain_list = []
    for domain, stats in domain_stats.items():
        domain_list.append({
            'domain': domain,
            'unique_pages': stats['count'],
            'total_visits': stats['total_visits'],
            'sample_titles': list(stats['titles'])[:5]  # Keep only 5 sample titles
        })
    
    # Sort by total visits
    domain_list.sort(key=lambda x: x['total_visits'], reverse=True)
    
    return domain_list[:top_n]

async def find_learning_paths(history_data: List[Dict]) -> List[Dict]:
    """Identify learning progressions in browsing history.
    
    Args:
        history_data: List of history entries from get_browser_history
    """
    
    # Common learning indicators in URLs
    learning_patterns = {
        'tutorial': r'tutorial|guide|learn|course',
        'documentation': r'docs|documentation|reference|api',
        'questions': r'stackoverflow|how-to|what-is|why-does',
        'examples': r'example|demo|sample|code',
        'video': r'youtube.*watch|video|lecture'
    }
    
    learning_sessions = []
    
    # Group by programming languages or technologies
    tech_patterns = {
        'python': r'python|django|flask|pandas|numpy',
        'javascript': r'javascript|js|react|vue|angular|node',
        'rust': r'rust-lang|rust',
        'go': r'golang|go-lang',
        'machine_learning': r'tensorflow|pytorch|scikit|ml|machine-learning',
        'web': r'html|css|web-dev|frontend|backend'
    }
    
    tech_visits = defaultdict(list)
    
    for entry in history_data:
        url_lower = entry['url'].lower()
        title_lower = (entry.get('title') or '').lower()
        
        # Check which technology this might be about
        for tech, pattern in tech_patterns.items():
            if re.search(pattern, url_lower) or re.search(pattern, title_lower):
                
                # Check what type of learning resource
                resource_type = 'general'
                for rtype, rpattern in learning_patterns.items():
                    if re.search(rpattern, url_lower):
                        resource_type = rtype
                        break
                
                tech_visits[tech].append({
                    'entry': entry,
                    'resource_type': resource_type
                })
    
    # Analyze progression for each technology
    for tech, visits in tech_visits.items():
        if len(visits) >= 3:  # Need at least 3 visits to show a pattern
            # Sort by time
            visits.sort(key=lambda x: x['entry']['last_visit_time'])
            
            learning_sessions.append({
                'technology': tech,
                'visit_count': len(visits),
                'resource_types': Counter(v['resource_type'] for v in visits),
                'time_span': {
                    'start': visits[0]['entry']['last_visit_time'],
                    'end': visits[-1]['entry']['last_visit_time']
                },
                'sample_resources': [v['entry'] for v in visits[:5]]
            })
    
    return learning_sessions

async def calculate_productivity_metrics(categorized_data: Dict[str, Dict]) -> Dict:
    """Calculate productivity metrics from categorized browsing data.
    
    Args:
        categorized_data: Categorized browsing data from categorize_browsing_history
    """
    
    productive_categories = {'development', 'learning', 'productivity'}
    unproductive_categories = {'social_media', 'entertainment', 'shopping'}
    
    total_visits = sum(cat['total_visits'] for cat in categorized_data.values())
    productive_visits = sum(categorized_data.get(cat, {}).get('total_visits', 0) 
                           for cat in productive_categories)
    unproductive_visits = sum(categorized_data.get(cat, {}).get('total_visits', 0) 
                             for cat in unproductive_categories)
    
    metrics = {
        'productivity_ratio': productive_visits / total_visits if total_visits > 0 else 0,
        'distraction_ratio': unproductive_visits / total_visits if total_visits > 0 else 0,
        'productive_visits': productive_visits,
        'unproductive_visits': unproductive_visits,
        'total_visits': total_visits,
        'top_productive_sites': [],
        'top_distraction_sites': []
    }
    
    # Get top sites from each category
    for cat in productive_categories:
        if cat in categorized_data:
            entries = categorized_data[cat]['entries']
            domains = Counter(urlparse(e['url']).netloc for e in entries)
            metrics['top_productive_sites'].extend(domains.most_common(3))
    
    for cat in unproductive_categories:
        if cat in categorized_data:
            entries = categorized_data[cat]['entries']
            domains = Counter(urlparse(e['url']).netloc for e in entries)
            metrics['top_distraction_sites'].extend(domains.most_common(3))
    
    return metrics

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

@mcp.tool()
async def analyze_browsing_sessions(
    history_data: List[Dict], 
    max_gap_hours: float = 2.0,
    include_patterns: bool = True
) -> List[Dict]:
    """
    Comprehensive session analysis combining time patterns, categories, and metrics.
    Returns enriched session data that's easy for Claude to interpret and report on.
    """
    
    if not history_data:
        return []
    
    # First, categorize all entries for lookup
    categorized_lookup = {}
    for entry in history_data:
        url = entry['url'].lower()
        domain = urlparse(url).netloc.lower()
        
        for category, config in BROWSING_CATEGORIES.items():
            if any(d in domain for d in config['domains']):
                categorized_lookup[entry['url']] = {
                    'category': category,
                    'subcategory': _get_subcategory(domain, config)
                }
                break
    
    # Sort by timestamp
    sorted_history = sorted(history_data, key=lambda x: x['last_visit_time'])
    
    sessions = []
    current_session = []
    
    for entry in sorted_history:
        visit_time = datetime.fromisoformat(entry['last_visit_time'])
        
        if not current_session:
            current_session = [entry]
        else:
            last_time = datetime.fromisoformat(current_session[-1]['last_visit_time'])
            gap_hours = (visit_time - last_time).total_seconds() / 3600
            
            if gap_hours <= max_gap_hours:
                current_session.append(entry)
            else:
                # Process completed session
                sessions.append(_enrich_session(current_session, categorized_lookup))
                current_session = [entry]
    
    # Don't forget the last session
    if current_session:
        sessions.append(_enrich_session(current_session, categorized_lookup))
    
    return sessions

def _enrich_session(session_entries: List[Dict], categorized_lookup: Dict) -> Dict:
    """
    Enrich a session with comprehensive analytics.
    This is where the magic happens for easy report generation.
    """
    start_time = datetime.fromisoformat(session_entries[0]['last_visit_time'])
    end_time = datetime.fromisoformat(session_entries[-1]['last_visit_time'])
    duration_minutes = (end_time - start_time).total_seconds() / 60
    
    # Category analysis
    category_counts = Counter()
    subcategory_counts = Counter()
    domains_visited = Counter()
    
    for entry in session_entries:
        domain = urlparse(entry['url']).netloc
        domains_visited[domain] += 1
        
        if entry['url'] in categorized_lookup:
            cat_info = categorized_lookup[entry['url']]
            category_counts[cat_info['category']] += 1
            if cat_info.get('subcategory'):
                subcategory_counts[cat_info['subcategory']] += 1
    
    # Determine session character
    total_entries = len(session_entries)
    productive_count = sum(category_counts.get(cat, 0) for cat in ['development', 'learning', 'productivity'])
    unproductive_count = sum(category_counts.get(cat, 0) for cat in ['social_media', 'entertainment', 'shopping'])
    
    # Session classification
    if productive_count > total_entries * 0.7:
        session_type = "highly_productive"
    elif productive_count > total_entries * 0.5:
        session_type = "mostly_productive"
    elif unproductive_count > total_entries * 0.7:
        session_type = "leisure"
    elif unproductive_count > total_entries * 0.5:
        session_type = "mostly_leisure"
    else:
        session_type = "mixed"
    
    # Time pattern analysis
    hour = start_time.hour
    day_of_week = start_time.strftime('%A')
    is_weekend = start_time.weekday() >= 5
    
    # Time of day classification
    if 5 <= hour < 9:
        time_period = "early_morning"
    elif 9 <= hour < 12:
        time_period = "morning"
    elif 12 <= hour < 13:
        time_period = "lunch"
    elif 13 <= hour < 17:
        time_period = "afternoon"
    elif 17 <= hour < 20:
        time_period = "evening"
    elif 20 <= hour < 23:
        time_period = "night"
    else:
        time_period = "late_night"
    
    # Focus analysis
    unique_domains = len(domains_visited)
    domain_switches = _count_domain_switches(session_entries)
    avg_time_per_domain = duration_minutes / unique_domains if unique_domains > 0 else 0
    
    # Identify if this was a "rabbit hole" session
    is_rabbit_hole = (
        unique_domains <= 3 and 
        duration_minutes > 30 and 
        max(domains_visited.values()) > 5
    )
    
    # Identify if this was a "research" session
    is_research = (
        category_counts.get('learning', 0) + category_counts.get('development', 0) > total_entries * 0.5 and
        unique_domains >= 5
    )
    
    return {
        # Basic info
        'session_id': f"{start_time.isoformat()}_{total_entries}",
        'start_time': start_time.isoformat(),
        'end_time': end_time.isoformat(),
        'duration_minutes': round(duration_minutes, 1),
        'entry_count': total_entries,
        
        # Time patterns
        'time_patterns': {
            'day_of_week': day_of_week,
            'is_weekend': is_weekend,
            'hour_of_day': hour,
            'time_period': time_period,
        },
        
        # Category analysis
        'category_distribution': dict(category_counts),
        'subcategory_distribution': dict(subcategory_counts),
        'dominant_category': category_counts.most_common(1)[0][0] if category_counts else 'uncategorized',
        'session_type': session_type,
        
        # Focus metrics
        'focus_metrics': {
            'unique_domains': unique_domains,
            'domain_switches': domain_switches,
            'avg_time_per_domain': round(avg_time_per_domain, 1),
            'top_domains': domains_visited.most_common(3),
            'focus_score': _calculate_focus_score(unique_domains, domain_switches, duration_minutes),
        },
        
        # Session characteristics
        'characteristics': {
            'is_rabbit_hole': is_rabbit_hole,
            'is_research': is_research,
            'is_productive': productive_count > unproductive_count,
            'productivity_ratio': round(productive_count / total_entries, 2) if total_entries > 0 else 0,
        },
        
        # Human-readable summary (for easy report generation)
        'summary': _generate_session_summary(
            session_type, time_period, duration_minutes, 
            category_counts.most_common(1)[0][0] if category_counts else 'browsing',
            is_rabbit_hole, is_research
        ),
        
        # Keep the entries for detailed analysis if needed
        'entries': session_entries
    }

def _count_domain_switches(entries: List[Dict]) -> int:
    """Count how many times the user switched between domains."""
    switches = 0
    last_domain = None
    
    for entry in entries:
        domain = urlparse(entry['url']).netloc
        if last_domain and domain != last_domain:
            switches += 1
        last_domain = domain
    
    return switches

def _calculate_focus_score(unique_domains: int, domain_switches: int, duration: float) -> float:
    """
    Calculate a focus score from 0-1.
    Lower scores = more focused, higher scores = more scattered.
    """
    if duration == 0:
        return 0
    
    # Normalize metrics
    switches_per_minute = domain_switches / duration
    domains_per_minute = unique_domains / duration
    
    # Focus score (inverted so higher is better)
    scatter_score = min(1.0, (switches_per_minute + domains_per_minute) / 2)
    return round(1 - scatter_score, 2)

def _generate_session_summary(
    session_type: str, 
    time_period: str, 
    duration: float,
    dominant_category: str,
    is_rabbit_hole: bool,
    is_research: bool
) -> str:
    """Generate a human-readable session summary."""
    
    # Build the summary
    parts = []
    
    # Duration descriptor
    if duration < 5:
        duration_desc = "quick"
    elif duration < 15:
        duration_desc = "short"
    elif duration < 45:
        duration_desc = "moderate"
    elif duration < 90:
        duration_desc = "long"
    else:
        duration_desc = "extended"
    
    # Main description
    if is_rabbit_hole:
        parts.append(f"A {duration_desc} {dominant_category} rabbit hole")
    elif is_research:
        parts.append(f"A {duration_desc} research session on {dominant_category}")
    else:
        parts.append(f"A {duration_desc} {session_type} session")
    
    # Time context
    parts.append(f"during the {time_period}")
    
    # Duration
    parts.append(f"({round(duration)} minutes)")
    
    return " ".join(parts)

def _get_subcategory(domain: str, config: Dict) -> Optional[str]:
    """Extract subcategory for a domain."""
    if 'subcategories' not in config:
        return None
    
    for subcat, patterns in config['subcategories'].items():
        if any(p in domain for p in patterns if isinstance(p, str)):
            return subcat
    
    return None

@mcp.tool()
def diagnose_safari_support() -> Dict[str, Any]:
    """Diagnose Safari support and accessibility. Useful for debugging Safari integration."""
    return check_safari_accessibility()


def _describe_typical_session(sessions: List[Dict]) -> str:
    """Generate a description of the typical browsing session."""
    if not sessions:
        return "No sessions found"
    
    avg_duration = sum(s['duration_minutes'] for s in sessions) / len(sessions)
    most_common_type = Counter(s['session_type'] for s in sessions).most_common(1)[0][0]
    most_common_time = Counter(s['time_patterns']['time_period'] for s in sessions).most_common(1)[0][0]
    
    return f"Typical session: {round(avg_duration)} minutes of {most_common_type} browsing, usually during {most_common_time}" 

def _generate_productivity_summary(sessions: List[Dict]) -> str:
    """Generate a productivity summary."""
    if not sessions:
        return "No sessions found"
    
    # filter sessions by productivity_ratio > 0.5
    productive_sessions = [s for s in sessions if s['characteristics']['productivity_ratio'] > 0.5]
    return f"Productivity summary: {round(sum(s['duration_minutes'] for s in productive_sessions))} minutes of productivity"

def _describe_time_habits(sessions: List[Dict]) -> str:
    """Generate a time habits summary."""
    if not sessions:
        return "No sessions found"
    
    # determine what times of days are correlated with each browsing category
    # Use a dict with categories as keys and a list of times of day as values
    time_habits = {}
    for session in sessions:
        for category, _ in BROWSING_CATEGORIES.items():
            if session['category_distribution'][category] > 0:
                time_habits[category].append(session['time_patterns']['time_period'])

    return f"Time habits summary: {time_habits}"

def _analyze_focus_patterns(sessions: List[Dict]) -> str:
    """Generate a focus patterns summary."""
    if not sessions:
        return "No sessions found"
    
    # determine times of day and duration of session that are most correlated with productivity_ratio
    # use a dict with times of day as keys and a list of durations as values
    focus_patterns = {}
    for session in sessions:
        if session['characteristics']['productivity_ratio'] > 0.5:
            focus_patterns[session['time_patterns']['time_period']].append(session['duration_minutes'])
    return f"Focus patterns summary: {focus_patterns}"

@mcp.tool()
async def get_browsing_insights(time_period_in_days: int = 7, analysis_types: List[str] = ["sessions", "categories", "domains", "learning_paths", "productivity"]) -> Dict[str, Any]:
    """Analyze browsing history based on selected analysis types.
    This tool will get the browser history from the specified browser(s) for the given time period.
    It will then group the history into sessions, categorize the history, analyze the domains, find learning paths, and calculate productivity metrics.
    It will return a dictionary with the following keys:
    - browsing_sessions: List of browsing sessions
    - categorized_data: Categorized browsing data
    - domain_stats: Domain statistics
    - learning_paths: Learning paths
    - productivity_metrics: Productivity metrics
    
    Args:
        history_data: List of history entries from get_browser_history
        analysis_types: List of analysis types to perform
    """

    history = await get_browser_history(time_period_in_days, "", True)
    
    # Use the new enriched session analysis
    enriched_sessions = await analyze_browsing_sessions(history)
    
    # Generate session-based insights
    session_insights = {
        'total_sessions': len(enriched_sessions),
        'avg_session_duration': sum(s['duration_minutes'] for s in enriched_sessions) / len(enriched_sessions) if enriched_sessions else 0,
        'session_types': Counter(s['session_type'] for s in enriched_sessions),
        'time_period_distribution': Counter(s['time_patterns']['time_period'] for s in enriched_sessions),
        'productive_sessions': sum(1 for s in enriched_sessions if s['characteristics']['is_productive']),
        'rabbit_holes': [s for s in enriched_sessions if s['characteristics']['is_rabbit_hole']],
        'research_sessions': [s for s in enriched_sessions if s['characteristics']['is_research']],
        'weekend_vs_weekday': {
            'weekend': [s for s in enriched_sessions if s['time_patterns']['is_weekend']],
            'weekday': [s for s in enriched_sessions if not s['time_patterns']['is_weekend']]
        }
    }
        # Still include other analyses for comprehensive view
    categorized_data = await categorize_browsing_history(history)
    domain_stats = await analyze_domain_frequency(history)
    learning_paths = await find_learning_paths(history)
    productivity_metrics = await calculate_productivity_metrics(categorized_data)
    
    return {
            "enriched_sessions": enriched_sessions,  # The new comprehensive sessions
            "session_insights": session_insights,     # Aggregated insights
            "categorized_data": categorized_data,
            "domain_stats": domain_stats,
            "learning_paths": learning_paths,
            "productivity_metrics": productivity_metrics,
            "report_helpers": {
                # Pre-formatted insights for easy report generation
                "typical_session": _describe_typical_session(enriched_sessions),
                "productivity_summary": _generate_productivity_summary(enriched_sessions),
                "time_habits": _describe_time_habits(enriched_sessions),
                "focus_analysis": _analyze_focus_patterns(enriched_sessions)
            }
        }

@mcp.tool()
async def search_browser_history(
    query: str,
    browser_history: List[Dict],
) -> List[Dict]:
    """This tool can only be used after the tool @get_browser_history has been used to get the browser history.
    It will search the browser history for the query and return the results.
    """     
    query_lower = query.lower()
    results = []
    
    for entry in browser_history:
        url = entry.get('url', '')
        title = entry.get('title', '')
        
        # Handle None values safely
        if (isinstance(url, str) and query_lower in url.lower()) or \
           (isinstance(title, str) and query_lower in title.lower()):
            results.append(entry)
    
    return results

        
if __name__ == "__main__":
    mcp.run()
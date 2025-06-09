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
from urllib.parse import urlparse
from collections import Counter, defaultdict
import re

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



@mcp.tool()
async def categorize_browsing_history(context: AppContext, history_data: List[Dict]) -> Dict[str, List[Dict]]:
    """Categorize URLs into meaningful groups"""
    
    categories = {
        'social_media': ['facebook.com', 'twitter.com', 'instagram.com', 'reddit.com', 'linkedin.com'],
        'entertainment': ['youtube.com', 'x.com', 'stardewvalleywiki.com'],
        'development': ['stackoverflow.com', 'developer.mozilla.org', 'docs.python.org'],
        'learning': ['coursera.org', 'udemy.com', 'khanacademy.org', 'medium.com', 'github.com'],
        'productivity': ['notion.so', 'trello.com', 'asana.com', 'todoist.com'],
        'news': ['nytimes.com', 'bbc.com', 'reuters.com', 'arstechnica.com'],
        'shopping': ['amazon.com', 'ebay.com', 'etsy.com', 'apple.com'],
        'search': ['google.com', 'bing.com', 'duckduckgo.com']
    }
    
    categorized = defaultdict(list)
    uncategorized = []
    
    for entry in history_data:
        domain = urlparse(entry['url']).netloc.lower()
        categorized_flag = False
        
        for category, domains in categories.items():
            if any(d in domain for d in domains):
                categorized[category].append(entry)
                categorized_flag = True
                break
        
        if not categorized_flag:
            uncategorized.append(entry)
    
    categorized['other'] = uncategorized
    
    # Add statistics
    result = {}
    for category, entries in categorized.items():
        result[category] = {
            'entries': entries,
            'count': len(entries),
            'unique_domains': len(set(urlparse(e['url']).netloc for e in entries)),
            'total_visits': sum(e.get('visit_count', 1) for e in entries)
        }
    
    return result

@mcp.tool()
async def analyze_domain_frequency(context: AppContext, history_data: List[Dict], top_n: int = 20) -> List[Dict]:
    """Analyze most frequently visited domains"""
    
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

@mcp.tool()
async def find_learning_paths(context: AppContext, history_data: List[Dict]) -> List[Dict]:
    """Identify learning progressions in browsing history"""
    
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

@mcp.tool()
async def calculate_productivity_metrics(context: AppContext, categorized_data: Dict[str, Dict]) -> Dict:
    """Calculate productivity metrics from categorized browsing data"""
    
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

if __name__ == "__main__":
    mcp.run()
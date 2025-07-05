from typing import Dict, List, Optional, TypedDict, Union
from dataclasses import dataclass
from datetime import datetime


# Type definitions for consistent data structures
class HistoryEntryDict(TypedDict):
    """Type for individual history entry as dictionary"""
    url: str
    title: Optional[str]
    visit_count: int
    last_visit_time: str  # ISO format datetime string

@dataclass(frozen=True)
class HistoryEntry:
    """Represents a single browser history entry"""
    url: str
    title: Optional[str]
    visit_count: int
    last_visit_time: datetime
    
    def to_dict(self) -> HistoryEntryDict:
        return {
            "url": self.url,
            "title": self.title,
            "visit_count": self.visit_count,
            "last_visit_time": self.last_visit_time.isoformat()
        }

def ensure_history_entry_dict(entry: Union[HistoryEntry, HistoryEntryDict]) -> HistoryEntryDict:
    """Convert HistoryEntry objects to dictionaries, pass through existing dicts"""
    if hasattr(entry, 'to_dict'):
        return entry.to_dict()
    return entry

class CategoryEntry(TypedDict):
    """Type for categorized entry within a category"""
    entries: List[HistoryEntryDict]
    subcategories: Dict[str, List[HistoryEntryDict]]
    count: int
    unique_domains: set
    total_visits: int

class DomainStat(TypedDict):
    """Type for domain statistics"""
    domain: str
    unique_pages: int
    total_visits: int
    sample_titles: List[str]

class LearningPath(TypedDict):
    """Type for learning path analysis"""
    technology: str
    visit_count: int
    resource_types: Dict[str, int]
    time_span: Dict[str, str]  # start and end as ISO strings
    sample_resources: List[HistoryEntryDict]

class ProductivityMetrics(TypedDict):
    """Type for productivity metrics"""
    productivity_ratio: float
    distraction_ratio: float
    productive_visits: int
    unproductive_visits: int
    total_visits: int
    top_productive_sites: List[tuple]
    top_distraction_sites: List[tuple]

class TimePatterns(TypedDict):
    """Type for time pattern analysis"""
    day_of_week: str
    is_weekend: bool
    hour_of_day: int
    time_period: str

class FocusMetrics(TypedDict):
    """Type for focus metrics"""
    unique_domains: int
    domain_switches: int
    avg_time_per_domain: float
    top_domains: List[tuple]
    focus_score: float

class SessionCharacteristics(TypedDict):
    """Type for session characteristics"""
    is_rabbit_hole: bool
    is_research: bool
    is_productive: bool
    productivity_ratio: float

class EnrichedSession(TypedDict):
    """Type for enriched session data"""
    session_id: str
    start_time: str  # ISO format
    end_time: str    # ISO format
    duration_minutes: float
    entry_count: int
    time_patterns: TimePatterns
    category_distribution: Dict[str, int]
    subcategory_distribution: Dict[str, int]
    dominant_category: str
    session_type: str
    focus_metrics: FocusMetrics
    characteristics: SessionCharacteristics
    summary: str
    entries: List[HistoryEntryDict]

class SessionInsights(TypedDict):
    """Type for aggregated session insights"""
    total_sessions: int
    avg_session_duration: float
    session_types: Dict[str, int]
    time_period_distribution: Dict[str, int]
    productive_sessions: int
    rabbit_holes: List[EnrichedSession]
    research_sessions: List[EnrichedSession]
    weekend_vs_weekday: Dict[str, List[EnrichedSession]]

class ReportHelpers(TypedDict):
    """Type for pre-formatted report helpers"""
    typical_session: str
    productivity_summary: str
    time_habits: str
    focus_analysis: str

class BrowserInsightsOutput(TypedDict):
    """Type for the complete output of get_browsing_insights"""
    enriched_sessions: List[EnrichedSession]
    session_insights: SessionInsights
    categorized_data: Dict[str, CategoryEntry]
    domain_stats: List[DomainStat]
    learning_paths: List[LearningPath]
    productivity_metrics: ProductivityMetrics
    report_helpers: ReportHelpers

class CachedHistoryMetadata(TypedDict):
    """Type for cached history metadata"""
    time_period_days: int
    fetched_at: str  # ISO format
    browser_type: str
    entry_count: int

@dataclass
class CachedHistory:
    history: List[HistoryEntryDict]
    metadata: CachedHistoryMetadata

    def __init__(self, history: List[HistoryEntryDict], time_period_in_days: int, browser_type: Optional[str] = None):
        self.history = history
        self.metadata = {
        'time_period_days': time_period_in_days,
        'fetched_at': datetime.now().isoformat(),
        'browser_type': browser_type or 'auto-detected',
        'entry_count': len(history)
    }

    def add_history(self, history: List[HistoryEntryDict], time_period_in_days: int, browser_type: Optional[str] = None):
        self.history = history
        self.metadata['entry_count'] = len(self.history)
        self.metadata['fetched_at'] = datetime.now().isoformat()
        self.metadata['time_period_days'] = time_period_in_days
        self.metadata['browser_type'] = browser_type or 'auto-detected'
    
    def get_history(self) -> List[HistoryEntryDict]:
        return self.history

    def has_history(self) -> bool:
        return len(self.history) > 0


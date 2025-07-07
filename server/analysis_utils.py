from typing import Dict, List, Optional, Any
from urllib.parse import urlparse
from collections import defaultdict, Counter
import re
import time
from datetime import datetime

from local_types import HistoryEntryDict, CategoryEntry, ensure_history_entry_dict, EnrichedSession, DomainStat, LearningPath, ProductivityMetrics, CachedHistory, BrowserInsightsOutput
from browser_utils import tool_get_browser_history
from BROWSING_CATEGORIES import BROWSING_CATEGORIES

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


async def categorize_browsing_history(history_data: List[HistoryEntryDict]) -> Dict[str, CategoryEntry]:
    """Categorize URLs into meaningful groups with patterns and subcategories.
    
    Args:
        history_data: List of history entries from get_browser_history
    """
    
    cat_start = time.time()
    print(f"📊 Categorization: Processing {len(history_data)} entries")
    
    categorized = defaultdict(lambda: {
        'entries': [],
        'subcategories': defaultdict(list),
        'count': 0,
        'unique_domains': set(),
        'total_visits': 0
    })
    
    uncategorized = []
    
    for raw_entry in history_data:
        # Allow HistoryEntry objects to be passed directly
        entry = ensure_history_entry_dict(raw_entry)

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
            'total_visits': sum(e.get('visit_count', 1) for e in uncategorized),
            'subcategories': {} # no subcategories for uncategorized
        }
   
    cat_time = time.time() - cat_start
    print(f"📊 Categorization: Completed in {cat_time:.3f}s, categorized {len(categorized)} categories")
    
    return dict(categorized)



async def analyze_domain_frequency(history_data: List[HistoryEntryDict], top_n: int = 20) -> List[DomainStat]:
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

async def find_learning_paths(history_data: List[HistoryEntryDict]) -> List[LearningPath]:
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

async def calculate_productivity_metrics(categorized_data: Dict[str, CategoryEntry]) -> ProductivityMetrics:
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

async def tool_analyze_browsing_sessions(history_data: List[HistoryEntryDict], max_gap_hours: float = 2.0) -> List[EnrichedSession]:
    if not history_data:
        return []
    
    session_start = time.time()
    
    # Limit to first 500 entries for faster processing
    limited_data = history_data[:500] if len(history_data) > 500 else history_data
    print(f"📊 Session Analysis: Processing {len(limited_data)} entries from {len(history_data)} total")
    
    # First, categorize all entries for lookup
    categorized_lookup = {}
    for entry in limited_data:
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
    sorted_history = sorted(limited_data, key=lambda x: x['last_visit_time'])
    
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
    
    session_time = time.time() - session_start
    print(f"📊 Session Analysis: Completed in {session_time:.3f}s, created {len(sessions)} sessions")
    
    return sessions

def _enrich_session(session_entries: List[HistoryEntryDict], categorized_lookup: Dict) -> EnrichedSession:
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

def _count_domain_switches(entries: List[HistoryEntryDict]) -> int:
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


def describe_typical_session(sessions: List[EnrichedSession]) -> str:
    """Generate a description of the typical browsing session."""
    if not sessions:
        return "No sessions found"
    
    avg_duration = sum(s['duration_minutes'] for s in sessions) / len(sessions)
    most_common_type = Counter(s['session_type'] for s in sessions).most_common(1)[0][0]
    most_common_time = Counter(s['time_patterns']['time_period'] for s in sessions).most_common(1)[0][0]
    
    return f"Typical session: {round(avg_duration)} minutes of {most_common_type} browsing, usually during {most_common_time}" 

def generate_productivity_summary(sessions: List[EnrichedSession]) -> str:
    """Generate a productivity summary."""
    if not sessions:
        return "No sessions found"
    
    # filter sessions by productivity_ratio > 0.5
    productive_sessions = [s for s in sessions if s['characteristics']['productivity_ratio'] > 0.5]
    return f"Productivity summary: {round(sum(s['duration_minutes'] for s in productive_sessions))} minutes of productivity"

def describe_time_habits(sessions: List[EnrichedSession]) -> str:
    """Generate a time habits summary."""
    if not sessions:
        return "No sessions found"
    
    # determine what times of days are correlated with each browsing category
    # Use a dict with categories as keys and a list of times of day as values
    time_habits = defaultdict(list)
    for session in sessions:
        for category, _ in BROWSING_CATEGORIES.items():
            if session['category_distribution'].get(category, 0) > 0:
                time_habits[category].append(session['time_patterns']['time_period'])

    return f"Time habits summary: {dict(time_habits)}"

def analyze_focus_patterns(sessions: List[EnrichedSession]) -> str:
    """Generate a focus patterns summary."""
    if not sessions:
        return "No sessions found"
    
    # determine times of day and duration of session that are most correlated with productivity_ratio
    # use a dict with times of day as keys and a list of durations as values
    focus_patterns = defaultdict(list)
    for session in sessions:
        if session['characteristics']['productivity_ratio'] > 0.5:
            focus_patterns[session['time_patterns']['time_period']].append(session['duration_minutes'])
    return f"Focus patterns summary: {dict(focus_patterns)}"

async def tool_get_browsing_insights(time_period_in_days: int, CACHED_HISTORY: CachedHistory, fast_mode: bool = True) -> BrowserInsightsOutput:
    start_time = time.time()
    benchmarks = {}
    
    # Step 1: Get history data
    step_start = time.time()
    if CACHED_HISTORY.metadata['time_period_days'] == time_period_in_days and CACHED_HISTORY.metadata['browser_type'] == "":
        history = CACHED_HISTORY.get_history()
        benchmarks["history_retrieval"] = time.time() - step_start
        print(f"📊 Benchmark: History retrieval (cached): {benchmarks['history_retrieval']:.3f}s")
    else:
        history_result = await tool_get_browser_history(time_period_in_days, CACHED_HISTORY, "", True)
        # Handle the new return type from tool_get_browser_history
        if isinstance(history_result, dict) and "history_entries" in history_result:
            history = history_result["history_entries"]
            # Log browser status for user awareness
            if history_result.get("failed_browsers"):
                print(f"⚠️  Some browsers failed: {history_result['failed_browsers']}. {history_result.get('recommendation', '')}")
        else:
            history = history_result  # Fallback for single browser mode
        benchmarks["history_retrieval"] = time.time() - step_start
        print(f"📊 Benchmark: History retrieval (fresh): {benchmarks['history_retrieval']:.3f}s")
    
    print(f"📊 Benchmark: History entries: {len(history)}")
    
    # Step 2: Limit history size for faster processing if fast_mode is enabled
    step_start = time.time()
    if fast_mode and len(history) > 1000:
        limited_history = history[:1000]
        performance_note = f"Analysis based on first 1000 entries from {len(history)} total entries for faster processing"
    else:
        limited_history = history
        performance_note = None
    benchmarks["data_limiting"] = time.time() - step_start
    print(f"📊 Benchmark: Data limiting: {benchmarks['data_limiting']:.3f}s")
    
    # Step 3: Session analysis (most likely bottleneck)
    step_start = time.time()
    enriched_sessions = await tool_analyze_browsing_sessions(limited_history)
    benchmarks["session_analysis"] = time.time() - step_start
    print(f"📊 Benchmark: Session analysis: {benchmarks['session_analysis']:.3f}s")
    print(f"📊 Benchmark: Sessions created: {len(enriched_sessions)}")
    
    # Step 4: Generate session insights
    step_start = time.time()
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
    benchmarks["session_insights"] = time.time() - step_start
    print(f"📊 Benchmark: Session insights generation: {benchmarks['session_insights']:.3f}s")
    
    # Step 5: Categorization
    step_start = time.time()
    categorized_data = await categorize_browsing_history(limited_history)
    benchmarks["categorization"] = time.time() - step_start
    print(f"📊 Benchmark: Categorization: {benchmarks['categorization']:.3f}s")
    
    # Step 6: Domain analysis
    step_start = time.time()
    domain_stats = await analyze_domain_frequency(limited_history, top_n=10)  # Reduce from 20 to 10
    benchmarks["domain_analysis"] = time.time() - step_start
    print(f"📊 Benchmark: Domain analysis: {benchmarks['domain_analysis']:.3f}s")
    
    # Step 7: Learning paths
    step_start = time.time()
    learning_paths = await find_learning_paths(limited_history)
    benchmarks["learning_paths"] = time.time() - step_start
    print(f"📊 Benchmark: Learning paths: {benchmarks['learning_paths']:.3f}s")
    
    # Step 8: Productivity metrics
    step_start = time.time()
    productivity_metrics = await calculate_productivity_metrics(categorized_data)
    benchmarks["productivity_metrics"] = time.time() - step_start
    print(f"📊 Benchmark: Productivity metrics: {benchmarks['productivity_metrics']:.3f}s")
    
    # Step 9: Report helpers
    step_start = time.time()
    report_helpers = {
        # Pre-formatted insights for easy report generation
        "typical_session": describe_typical_session(enriched_sessions),
        "productivity_summary": generate_productivity_summary(enriched_sessions),
        "time_habits": describe_time_habits(enriched_sessions),
        "focus_analysis": analyze_focus_patterns(enriched_sessions)
    }
    benchmarks["report_helpers"] = time.time() - step_start
    print(f"📊 Benchmark: Report helpers: {benchmarks['report_helpers']:.3f}s")
    
    # Total time
    total_time = time.time() - start_time
    benchmarks["total_time"] = total_time
    print(f"📊 Benchmark: TOTAL TIME: {total_time:.3f}s")
    
    # Performance summary
    print("\n📊 PERFORMANCE SUMMARY:")
    sorted_benchmarks = sorted(benchmarks.items(), key=lambda x: x[1], reverse=True)
    for step, duration in sorted_benchmarks:
        if step != "total_time":
            percentage = (duration / total_time) * 100
            print(f"  {step}: {duration:.3f}s ({percentage:.1f}%)")
    
    new_history = {
            "enriched_sessions": enriched_sessions,  # The new comprehensive sessions
            "session_insights": session_insights,     # Aggregated insights
            "categorized_data": categorized_data,
            "domain_stats": domain_stats,
            "learning_paths": learning_paths,
            "productivity_metrics": productivity_metrics,
            "report_helpers": report_helpers,
            "benchmarks": benchmarks  # Include benchmarks in output
        }  # type: BrowserInsightsOutput
    
    # Cache the history for future use
    CACHED_HISTORY.add_history(history, time_period_in_days, "")
    
    # Add performance note if we limited the data
    if performance_note:
        new_history["performance_note"] = performance_note
    
    return new_history
    
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
        # Limit history size for faster processing if fast_mode is enabled
    if fast_mode and len(history) > 1000:
        limited_history = history[:1000]
        performance_note = f"Analysis based on first 1000 entries from {len(history)} total entries for faster processing"
    else:
        limited_history = history
        performance_note = None
    
    # Still include other analyses for comprehensive view
    categorized_data = await categorize_browsing_history(limited_history)
    domain_stats = await analyze_domain_frequency(limited_history, top_n=10)  # Reduce from 20 to 10
    learning_paths = await find_learning_paths(limited_history)
    productivity_metrics = await calculate_productivity_metrics(categorized_data)
    
    new_history = {
            "enriched_sessions": enriched_sessions,  # The new comprehensive sessions
            "session_insights": session_insights,     # Aggregated insights
            "categorized_data": categorized_data,
            "domain_stats": domain_stats,
            "learning_paths": learning_paths,
            "productivity_metrics": productivity_metrics,
            "report_helpers": {
                # Pre-formatted insights for easy report generation
                "typical_session": describe_typical_session(enriched_sessions),
                "productivity_summary": generate_productivity_summary(enriched_sessions),
                "time_habits": describe_time_habits(enriched_sessions),
                "focus_analysis": analyze_focus_patterns(enriched_sessions)
            }
        }  # type: BrowserInsightsOutput
    
    # Cache the history for future use
    CACHED_HISTORY.add_history(history, time_period_in_days, "")
    
    # Add performance note if we limited the data
    if performance_note:
        new_history["performance_note"] = performance_note
    
    return new_history

async def tool_suggest_personalized_browser_categories(CACHED_HISTORY: CachedHistory) -> List[str]:

    if not CACHED_HISTORY.has_history():
        raise RuntimeError("No history found. Please run @get_browsing_insights first.")

    # Categorize the history to find the uncategorized bucket
    history = CACHED_HISTORY.get_history()
    categorized_data = await categorize_browsing_history(history)

    # `other` holds anything we failed to classify
    uncategorized_entries = categorized_data.get("other", {}).get("entries", [])

    # Extract just the URLs so we can return them to the user
    new_categories = [e["url"] for e in uncategorized_entries]

    return {"URLs without categories": new_categories}

async def tool_get_quick_insights(time_period_in_days: int, CACHED_HISTORY: CachedHistory) -> Dict[str, Any]:
    """Get quick browser history insights with minimal processing for fast results."""
    
    # Get history data
    if CACHED_HISTORY.metadata['time_period_days'] == time_period_in_days and CACHED_HISTORY.metadata['browser_type'] == "":
        history = CACHED_HISTORY.get_history()
    else:
        history_result = await tool_get_browser_history(time_period_in_days, CACHED_HISTORY, "", True)
        if isinstance(history_result, dict) and "history_entries" in history_result:
            history = history_result["history_entries"]
            browser_status = history_result
        else:
            history = history_result
            browser_status = None
    
    if not history:
        return {"error": "No history data available"}
    
    # Limit to first 500 entries for speed
    limited_history = history[:500] if len(history) > 500 else history
    
    # Basic statistics
    total_entries = len(limited_history)
    unique_domains = len(set(urlparse(entry['url']).netloc for entry in limited_history))
    
    # Top domains (simple count)
    domain_counts = {}
    for entry in limited_history:
        domain = urlparse(entry['url']).netloc
        domain_counts[domain] = domain_counts.get(domain, 0) + 1
    
    top_domains = sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Basic categorization (simplified)
    categories = {"work": 0, "social": 0, "entertainment": 0, "other": 0}
    for entry in limited_history:
        url = entry['url'].lower()
        domain = urlparse(url).netloc.lower()
        
        if any(d in domain for d in ['github.com', 'stackoverflow.com', 'docs.', 'api.']):
            categories["work"] += 1
        elif any(d in domain for d in ['facebook.com', 'twitter.com', 'instagram.com', 'reddit.com']):
            categories["social"] += 1
        elif any(d in domain for d in ['youtube.com', 'netflix.com', 'spotify.com']):
            categories["entertainment"] += 1
        else:
            categories["other"] += 1
    
    result = {
        "total_entries": total_entries,
        "unique_domains": unique_domains,
        "top_domains": top_domains,
        "category_breakdown": categories,
        "time_period_days": time_period_in_days,
        "processing_note": f"Quick analysis of first {len(limited_history)} entries from {len(history)} total entries"
    }
    
    # Add browser status if available
    if browser_status and browser_status.get("failed_browsers"):
        result["browser_status"] = browser_status
    
    return result


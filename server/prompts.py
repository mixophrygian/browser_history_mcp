PRODUCTIVITY_ANALYSIS_PROMPT = """
    Analyze the browser history to provide actionable productivity insights.

    The MCP tool @get_browsing_insights will be used to get the browser history and insights.
        
    Then provide:

    1. **Browsers Available**
       - List the browsers that you were able to retrieve history from.
       - If you were unable to retrieve history from a browser that was detected, explain why, and note that it probably contains history that is worth considering..
    
    2. **Time Distribution Analysis**
       - Calculate percentage of time on work-related vs entertainment sites
       - Identify peak productivity hours based on work-site visits
       - Show time spent per domain/category
    
    3. **Session Pattern Recognition**
       - Group visits into sessions (max 2-hour gaps between visits)
       - Identify "rabbit hole" sessions (many related searches in sequence)
       - Flag sessions that started productive but drifted
    
   4. **Focus Metrics**
       - Average session duration on productive sites
       - Number of context switches between work and entertainment
       - Longest uninterrupted work sessions
    
   5. **Actionable Recommendations**
       - Top 3 time-sink websites to consider blocking
       - Optimal work hours based on historical patterns
       - Specific habits to change (e.g., "You check Reddit 15x/day on average")
    
    Present findings in a clear format with specific numbers and time periods.
    """

LEARNING_ANALYSIS_PROMPT = """
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

RESEARCH_TOPIC_EXTRACTION_PROMPT = """
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

GENERATE_INSIGHTS_REPORT_PROMPT = """
    Create a personalized insights report based on your browsing patterns:

    1. **Overview Summary**
       - Total browsing time and active days
       - Most visited categories and domains
       - Peak activity periods and patterns

    2. **Productivity Metrics**
       - Work/learning vs entertainment balance
       - Focus periods and distraction patterns
       - Context switching frequency and impact

    3. **Content Consumption Analysis**
       - Types of content most frequently accessed
       - Time distribution across media types
       - Reading vs interactive content patterns

    4. **Behavioral Patterns**
       - Daily and weekly routines
       - Common browsing sequences
       - Habit triggers and patterns

    5. **Personalized Recommendations**
       - Suggested schedule optimizations
       - Focus improvement opportunities
       - Content consumption balancing tips

    Present as a comprehensive report with data visualizations and actionable insights.
    """

COMPARE_TIME_PERIODS_PROMPT = """
    Compare your browsing habits across different time periods:

    1. **Time Period Analysis**
       - Compare daily/weekly/monthly patterns
       - Identify significant behavior changes
       - Track long-term trends and shifts

    2. **Category Evolution**
       - Changes in category time distribution
       - New or abandoned interests
       - Shifting productivity patterns

    3. **Habit Transformation**
       - Progress on reducing time-sink websites
       - Improvements in focus metrics
       - Changes in learning patterns

    4. **Productivity Trends**
       - Work efficiency changes
       - Focus session duration trends
       - Context switching frequency changes

    5. **Impact Assessment**
       - Effectiveness of previous recommendations
       - Progress towards goals
       - Areas needing continued attention

    Format as a comparative analysis with clear before/after metrics and trend visualization suggestions.
    """

EXPORT_VISUALIZATION_PROMPT = """
    Export your browsing data as interactive visualizations:

    1. **Time-Based Visualizations**
       - Daily/weekly activity heatmaps
       - Category distribution timelines
       - Peak usage period charts

    2. **Network Analysis**
       - Domain relationship networks
       - Category interaction flows
       - Session transition maps

    3. **Pattern Visualizations**
       - Focus/distraction cycle plots
       - Learning progression graphs
       - Productivity trend lines

    4. **Interactive Elements**
       - Time period selectors
       - Category filters
       - Drill-down capabilities

    5. **Export Options**
       - Interactive HTML dashboards
       - Static report PDFs
       - Raw data exports

    Include specific visualization recommendations based on the data patterns identified.
    """
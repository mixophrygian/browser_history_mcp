PRODUCTIVITY_ANALYSIS_PROMPT = """
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
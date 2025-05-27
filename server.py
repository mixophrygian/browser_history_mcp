import sqlite3
import os
import enum
from contextlib import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
import logging
from mcp.server.fastmcp import FastMCP, Context

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger("browser-storage-mcp")

FIREFOX_PROFILE_DIR = "`/Users/eleanor.mazzarella/Library/Application Support/Firefox/Profiles/l42msng6.default-release`" 

PATH_TO_FIREFOX_HISTORY = os.path.join(FIREFOX_PROFILE_DIR, "places.sqlite")

@dataclass(frozen=True)
class BrowserType(enum.Enum):
    FIREFOX = "firefox"
    CHROME = "chrome" 


mcp = FastMCP("firefox-history")

@dataclass
class AppContext:
    db: sqlite3.Connection

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with type-safe context"""
    # initialize on startup
    db = sqlite3.connect(PATH_TO_FIREFOX_HISTORY)
    try: 
        yield AppContext(db=db)
    finally:
        db.close()


# pass lifespan to server
mcp = FastMCP("firefox-history", lifespan=app_lifespan)

@mcp.prompt()
def productivity_analysis() -> str:
    """Creates a user prompt for analyzing productivity"""
    return """
    Focus on work vs. entertainment ratios, identify time sinks, suggest optimizations.
    Group history by "session", which can be inferred by the gap between timestamps.
    For example, a "session" might be a period of time with no more than 2 hours between visits.
    """

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


@mcp.tool()
async def get_browser_history(context: AppContext, time_period_in_days: int, browser_type: BrowserType) -> list[str]:
    """Get history from Firefox or Chrome"""
    cursor = context.db.cursor()
# TODO
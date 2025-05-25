import sqlite3
import os
from contextlib import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
import logging
from mcp.server.fastmcp import FastMCP, Context


FIREFOX_PROFILE_DIR = "`/Users/eleanor.mazzarella/Library/Application Support/Firefox/Profiles/l42msng6.default-release`" 

PATH_TO_FIREFOX_HISTORY = os.path.join(FIREFOX_PROFILE_DIR, "places.sqlite")

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger("browser-storage-mcp")

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
def explore_firefox_history() -> str:
    """Create a prompt to explore the Firefox history"""
    return """
    I can help you explore your Firefox history.  

    Here are some of the things I can do:
    - I can list all of the sites you visited today or in the last week.
    """

@mcp.prompt()
def analyze_firefox_history(number_of_days: int) -> str:
    """Analyze the Firefox history"""
    return f"""
    I can analyze the Firefox history from the past '{number_of_days}' days.

    I can help you understand:
    - What sites you visited the most
    - What common themes arise from your browsing history
    - Areas you have been focusing on in the past {number_of_days} days
    """

@mcp.prompt()
def create_firefox_history_report(number_of_days: int) -> str:
    """Create a report of the Firefox history"""
    return f"""
    I can create a report of the Firefox history from the past '{number_of_days}' days.

    The report will be in markdown with a clear structure, and will be saved to a file in the current directory.
    """



@mcp.tool()
async def get_history(context: AppContext, query: str) -> list[str]:
    """Get history from Firefox"""
    cursor = context.db.cursor()
    cursor.execute("SELECT url FROM moz_places WHERE url LIKE ?", (f"%{query}%",))
    return [row[0] for row in cursor.fetchall()]
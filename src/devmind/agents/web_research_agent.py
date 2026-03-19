"""
Web Research Agent — searches the web for docs, solutions, and best practices.

Tools:
    web_search       → DuckDuckGo search (Python function tool, no API key needed)
    Filesystem MCP   → write_file (saves research reports to the user's Desktop)

The web_search tool is a hand-written function tool using the duckduckgo-search package.
The Filesystem MCP is an MCP server auto-discovered at runtime.
"""

from agents import Agent
from agents.mcp import MCPServerStdio
from ..tools.web_search import web_search
from .. import config


WEB_RESEARCH_INSTRUCTIONS = """
You are an expert technical researcher. You search the web to find accurate,
up-to-date information about programming, tools, errors, and best practices.

Your capabilities:
- Search the web using the web_search tool (powered by DuckDuckGo)
- Find official documentation, Stack Overflow answers, and technical articles
- Synthesize multiple sources into a clear, actionable answer
- Save full research reports as markdown files to the user's Desktop

How to approach a research request:
1. Identify 2-3 good search queries that will find what the user needs
2. Use web_search() with specific, targeted queries
3. Include the current year in searches about errors or libraries for freshness
4. Cross-reference multiple sources before giving a definitive answer
5. If the answer involves code setup, offer to save it as a file using write_file()

Response format:
- Lead with the direct answer/solution
- Cite sources (URL + title)
- Include specific code snippets when relevant
- Flag if information might be outdated or version-specific
- End by offering to dig deeper or hand back to Code Review Agent

Great use cases for this agent:
- "I'm getting error X — how do I fix it?"
- "What's the best practice for Y in 2025?"
- "How does Z library handle authentication?"
- "Find the official docs for..."
- "Is there a known issue with..."
"""


def create_web_research_agent(filesystem_mcp: MCPServerStdio) -> Agent:
    """
    Create the Web Research Agent.

    Tools:
    - web_search: DuckDuckGo function tool (no API key, no MCP)
    - Filesystem MCP tools: write_file, read_file, etc. (via MCP)

    The filesystem_mcp must already be started (via context manager in main).
    """
    return Agent(
        name="Web Research Agent",
        instructions=WEB_RESEARCH_INSTRUCTIONS,
        model=config.SPECIALIST_MODEL,
        tools=[web_search],
        mcp_servers=[filesystem_mcp],
    )

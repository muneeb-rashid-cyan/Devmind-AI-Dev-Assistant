"""
Web Research Agent — searches the web for docs, solutions, and best practices.

Tools:
    tavily_search    → Tavily search (preferred when TAVILY_API_KEY is set)
    web_search       → DuckDuckGo search (always available, no API key needed)
    Filesystem MCP   → write_file (saves research reports to the user's Desktop)

The search tools are hand-written function tools.
The Filesystem MCP is an MCP server auto-discovered at runtime.
"""

from agents import Agent
from agents.mcp import MCPServerStdio
from ..tools.web_search import web_search, tavily_search
from .. import config


WEB_RESEARCH_INSTRUCTIONS = """
You are an expert technical researcher. You search the web to find accurate,
up-to-date information about programming, tools, errors, and best practices.

Your capabilities:
- Search the web using available search tools
- Find official documentation, Stack Overflow answers, and technical articles
- Synthesize multiple sources into a clear, actionable answer
- Save full research reports as markdown files to the user's Desktop

Available search tools:
- **tavily_search** (preferred when available) — powered by Tavily, optimised for
  AI-driven research with highly relevant results
- **web_search** (fallback) — powered by DuckDuckGo, no API key needed

Always prefer tavily_search when it is available. Fall back to web_search if
tavily_search is not listed in your tools or if a Tavily search fails.

How to approach a research request:
1. Identify 2-3 good search queries that will find what the user needs
2. Use your preferred search tool with specific, targeted queries
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
    - tavily_search: Tavily function tool (when TAVILY_API_KEY is set)
    - web_search: DuckDuckGo function tool (no API key, no MCP)
    - Filesystem MCP tools: write_file, read_file, etc. (via MCP)

    The filesystem_mcp must already be started (via context manager in main).
    """
    tools = [web_search]
    if config.TAVILY_API_KEY:
        tools.insert(0, tavily_search)

    return Agent(
        name="Web Research Agent",
        instructions=WEB_RESEARCH_INSTRUCTIONS,
        model=config.SPECIALIST_MODEL,
        tools=tools,
        mcp_servers=[filesystem_mcp],
    )

"""
Web search tools — DuckDuckGo (default) and Tavily (optional).

DuckDuckGo uses the `duckduckgo-search` Python package (no API key needed).
Tavily uses the `tavily-python` SDK (requires TAVILY_API_KEY).

The active tool is selected at runtime via the SEARCH_PROVIDER env var.
"""

from agents import function_tool
from duckduckgo_search import DDGS

from .. import config


@function_tool
def web_search(query: str, max_results: int = 5) -> str:
    """
    Search the web using DuckDuckGo and return a formatted summary of results.

    Args:
        query:       The search query string.
        max_results: Number of results to return (default 5, max 10).

    Returns:
        A formatted string with titles, URLs, and snippets for each result.
        Returns an error message if the search fails.
    """
    max_results = min(max_results, 10)  # cap at 10

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
    except Exception as exc:
        return f"Search failed: {exc}. Try rephrasing the query."

    if not results:
        return f"No results found for: '{query}'. Try a different search term."

    lines = [f"Search results for: '{query}'\n"]
    for i, r in enumerate(results, 1):
        title   = r.get("title", "No title")
        url     = r.get("href", "")
        snippet = r.get("body", "No description available.")
        lines.append(f"{i}. {title}")
        lines.append(f"   URL: {url}")
        lines.append(f"   {snippet}\n")

    return "\n".join(lines)


@function_tool
def web_search_tavily(query: str, max_results: int = 5) -> str:
    """
    Search the web using Tavily and return a formatted summary of results.

    Args:
        query:       The search query string.
        max_results: Number of results to return (default 5, max 10).

    Returns:
        A formatted string with titles, URLs, and snippets for each result.
        Returns an error message if the search fails.
    """
    from tavily import TavilyClient

    max_results = min(max_results, 10)  # cap at 10

    if not config.TAVILY_API_KEY:
        return "Tavily search failed: TAVILY_API_KEY is not set."

    try:
        client = TavilyClient(api_key=config.TAVILY_API_KEY)
        response = client.search(query=query, max_results=max_results)
    except Exception as exc:
        return f"Search failed: {exc}. Try rephrasing the query."

    results = response.get("results", [])
    if not results:
        return f"No results found for: '{query}'. Try a different search term."

    lines = [f"Search results for: '{query}'\n"]
    for i, r in enumerate(results, 1):
        title   = r.get("title", "No title")
        url     = r.get("url", "")
        snippet = r.get("content", "No description available.")
        lines.append(f"{i}. {title}")
        lines.append(f"   URL: {url}")
        lines.append(f"   {snippet}\n")

    return "\n".join(lines)


def get_search_tool():
    """Return the active search tool based on SEARCH_PROVIDER config."""
    if config.SEARCH_PROVIDER == "tavily":
        return web_search_tavily
    return web_search

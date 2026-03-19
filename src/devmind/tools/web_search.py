"""
DuckDuckGo web search tool — no API key required.

Uses the `duckduckgo-search` Python package which scrapes DuckDuckGo.
Exposed as a function tool so the Web Research Agent can call it directly.
"""

from agents import function_tool
from duckduckgo_search import DDGS


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

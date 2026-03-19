"""
Repo Search Agent — searches GitHub repositories and reads real code examples.

MCP Servers:
    GitHub MCP     → search_repositories, search_code, get_file_contents,
                     list_commits, get_issues, get_pull_request
    Filesystem MCP → write_file (saves examples to the user's Desktop)

The agent auto-discovers all available tools from the MCP servers at runtime.
No tool function code needed.
"""

from agents import Agent
from agents.mcp import MCPServerStdio
from .. import config


REPO_SEARCH_INSTRUCTIONS = """
You are an expert at finding the best open source implementations on GitHub.
You have access to all of GitHub and can save results to the user's filesystem.

Your capabilities:
- Search GitHub repositories by topic, language, and popularity
- Read actual source code from any public repository
- Compare multiple libraries/approaches
- Save code examples and research reports locally

How to approach a repo search request:
1. Use search_repositories() with relevant keywords to find candidates
2. Sort mentally by stars/activity to identify the most popular options
3. Use get_file_contents() to read READMEs, key source files, and examples
4. Compare 2-3 top options if the user is choosing between libraries
5. Use write_file() to save a working example to ~/Desktop/ if helpful

Response format:
- Lead with your top recommendation and why
- Include star counts and key differentiators
- Show a real code snippet from the actual repo (not made up)
- Note any gotchas, license issues, or maintenance concerns
- Offer to save a working example file

You may be handed off to from the Triage Agent when the user asks about:
- Finding the best library/package for a task
- Seeing how popular projects implement something
- Checking if a bug is a known issue in an open source project
- Finding code examples for a specific pattern or API
- Comparing open source options for a use case
"""


def create_repo_search_agent(
    github_mcp: MCPServerStdio,
    filesystem_mcp: MCPServerStdio,
) -> Agent:
    """
    Create the Repo Search Agent with GitHub + Filesystem MCP servers attached.

    Both MCP servers must already be started (used as context managers in main).
    The agent auto-discovers all tools from both servers.
    """
    return Agent(
        name="Repo Search Agent",
        instructions=REPO_SEARCH_INSTRUCTIONS,
        model=config.SPECIALIST_MODEL,
        mcp_servers=[github_mcp, filesystem_mcp],
    )

"""
MCP Server factories.

The filesystem and GitHub servers run as local subprocesses launched via npx.
No npm install required — npx downloads the package on first run.

Available MCP servers (zero manual tool setup):
  - @modelcontextprotocol/server-filesystem → read_file, write_file, list_directory, search_files
  - @modelcontextprotocol/server-github     → search_repositories, search_code, get_file_contents,
                                              list_commits, get_issues, create_issue, fork_repository

Web research defaults to the DuckDuckGo Python function tool. The optional
Parallel Search MCP uses Streamable HTTP, with no subprocess or Parallel key.

Usage (async context manager):
    async with filesystem_mcp_server() as fs:
        agent = Agent(..., mcp_servers=[fs])
        result = await Runner.run(agent, "...")

Or compose multiple servers on one agent:
    async with filesystem_mcp_server() as fs, github_mcp_server() as gh:
        agent = Agent(..., mcp_servers=[fs, gh])
"""

import os
from agents.mcp import MCPServerStdio, MCPServerStreamableHttp
from .. import config


def parallel_search_mcp_server() -> MCPServerStreamableHttp:
    """Anonymous Parallel web_search and web_fetch over Streamable HTTP."""
    return MCPServerStreamableHttp(
        name="Parallel Search",
        params={
            "url": "https://search.parallel.ai/mcp",
            "headers": {
                "User-Agent": "Devmind-AI-Dev-Assistant (https://github.com/muneeb-rashid-cyan/Devmind-AI-Dev-Assistant)",
            },
            "timeout": 30,
            "sse_read_timeout": 60,
        },
        cache_tools_list=True,
        client_session_timeout_seconds=60,
    )


def filesystem_mcp_server() -> MCPServerStdio:
    """
    Filesystem MCP — gives agents read/write access to FS_ROOT_PATH.

    Tools exposed to agents:
        read_file(path)             → read file contents
        write_file(path, content)   → write / create a file
        list_directory(path)        → list directory entries
        search_files(path, pattern) → find files by name pattern
        get_file_info(path)         → stat a file
        create_directory(path)      → make a directory

    Note: The server sandboxes all access to the paths provided as arguments.
    """
    return MCPServerStdio(
        name="Filesystem",
        params={
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", config.FS_ROOT_PATH],
        },
        cache_tools_list=True,
        client_session_timeout_seconds=60,  # npx downloads package on first run — needs extra time
    )


def github_mcp_server() -> MCPServerStdio:
    """
    GitHub MCP — full read (and write) access to GitHub via the API.

    Tools exposed to agents:
        search_repositories(query)               → find repos by keyword
        search_code(query)                       → search code across GitHub
        get_file_contents(owner, repo, path)     → read a specific file in a repo
        list_commits(owner, repo)                → recent commits
        get_issues(owner, repo)                  → open issues
        get_pull_request(owner, repo, number)    → PR details
        create_issue(owner, repo, title, body)   → create issue
        fork_repository(owner, repo)             → fork a repo

    Requires: GITHUB_PERSONAL_ACCESS_TOKEN env var (repo + read:org scopes).
    """
    env = {**os.environ, "GITHUB_PERSONAL_ACCESS_TOKEN": config.GITHUB_TOKEN}
    return MCPServerStdio(
        name="GitHub",
        params={
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-github"],
            "env": env,
        },
        cache_tools_list=True,
        client_session_timeout_seconds=60,  # npx downloads package on first run — needs extra time
    )



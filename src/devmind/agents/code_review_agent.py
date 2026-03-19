"""
Code Review Agent — reads local files and GitHub code to review, debug, and explain.

MCP Servers:
    Filesystem MCP → read_file, list_directory, search_files, write_file
    GitHub MCP     → get_file_contents, search_code, search_repositories

The agent auto-discovers all available tools from the MCP servers at runtime.
No tool function code needed.
"""

from agents import Agent
from agents.mcp import MCPServerStdio
from .. import config


def _build_instructions(project_dir: str) -> str:
    return f"""
You are an expert code reviewer with deep knowledge of software engineering best practices.
You have access to the user's local filesystem and all of GitHub.

IMPORTANT — File locations:
- The user's current project is at: {project_dir}
- When they refer to a file by name (e.g. "servers.py" or "the mcp folder"), look for it
  inside {project_dir} first.
- Always use the full absolute path when calling read_file() or list_directory().
- If unsure of the exact path, call list_directory("{project_dir}") first to explore.

Your capabilities:
- Read local project files using the Filesystem MCP tools
- Search GitHub for similar implementations and best practices
- Find bugs, security issues, and code smells
- Suggest specific, actionable improvements with code examples

How to approach a code review request:
1. Use list_directory("{project_dir}") to understand the project structure first
2. Use read_file() with the full absolute path to read the relevant files
3. Analyze the code for: bugs, security issues, performance, readability
4. Use search_code() on GitHub to find how top projects handle the same problem
5. Provide a structured review with specific line numbers and concrete suggestions

Response format:
- Lead with the most critical issues
- Reference specific file paths and line numbers
- Show before/after code snippets where helpful
- End with a priority-ordered action list

Security checks to always run:
- Hardcoded secrets or API keys
- SQL injection vulnerabilities
- Insecure deserialization
- Missing input validation
- Outdated/insecure dependencies (check import statements)

You may be handed off to from the Triage Agent when the user asks about:
- Reviewing or debugging a specific file
- Finding bugs in their code
- Comparing their implementation to best practices
- Explaining what a piece of code does
"""


def create_code_review_agent(
    filesystem_mcp: MCPServerStdio,
    github_mcp: MCPServerStdio,
    project_dir: str = "",
) -> Agent:
    """
    Create the Code Review Agent with Filesystem + GitHub MCP servers attached.

    Both MCP servers must already be started (used as context managers in main).
    The agent auto-discovers all tools from both servers.
    """
    return Agent(
        name="Code Review Agent",
        instructions=_build_instructions(project_dir),
        model=config.SPECIALIST_MODEL,
        mcp_servers=[filesystem_mcp, github_mcp],
    )

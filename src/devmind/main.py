"""
DevMind — AI-Powered Personal Dev Assistant
Entry point for the interactive CLI.

Run:
    python -m src.devmind.main

Controls:
    Type your question and press ENTER
    Type 'exit' or 'quit' to stop
    Type 'clear' to start a new session
    Ctrl+C to force quit

Architecture:
    Your input
        → Triage Agent (GPT-4o-mini, routes the request)
            ├── Code Review Agent  → Filesystem MCP + GitHub MCP
            ├── Repo Search Agent  → GitHub MCP + Filesystem MCP
            └── Web Research Agent → DuckDuckGo tool + Filesystem MCP
        → SQLiteSession (persists conversation history)
        → Printed response
"""

import asyncio
import os
import sys
from contextlib import AsyncExitStack

from agents import Runner, InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered

from .mcp.servers import filesystem_mcp_server, github_mcp_server
from .agents.code_review_agent import create_code_review_agent
from .agents.repo_search_agent import create_repo_search_agent
from .agents.web_research_agent import create_web_research_agent
from .agents.triage_agent import create_triage_agent
from .session.memory import get_session
from . import config


# ── ANSI colors (no extra dependency) ─────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
DIM    = "\033[2m"


def _print_banner() -> None:
    print(f"\n{BOLD}{CYAN}{'═' * 58}{RESET}")
    print(f"{BOLD}{CYAN}   DevMind — AI-Powered Personal Dev Assistant{RESET}")
    print(f"{BOLD}{CYAN}   Powered by OpenAI Agents SDK + MCP{RESET}")
    print(f"{BOLD}{CYAN}{'═' * 58}{RESET}")
    print(f"  {DIM}Session : {config.SESSION_ID}{RESET}")
    print(f"  {DIM}Memory  : {config.DB_PATH}{RESET}")
    print(f"  {DIM}FS Root : {config.FS_ROOT_PATH}{RESET}")
    print(f"{BOLD}{CYAN}{'═' * 58}{RESET}")
    print(f"\n  {DIM}MCP Servers starting...{RESET}", flush=True)


def _print_agents_ready() -> None:
    print(f"\n  {GREEN}✓ Filesystem MCP   — local file access{RESET}")
    print(f"  {GREEN}✓ GitHub MCP       — repo search + code read{RESET}")
    print(f"  {GREEN}✓ DuckDuckGo tool  — web search (no API key){RESET}")
    print(f"\n  {BOLD}Agents ready:{RESET}")
    print(f"  {CYAN}Triage{RESET} → {GREEN}Code Review{RESET} | {GREEN}Repo Search{RESET} | {GREEN}Web Research{RESET}")
    print(f"\n  {DIM}Type your question. 'exit' to quit. 'clear' for new session.{RESET}\n")


def _print_separator() -> None:
    print(f"\n{DIM}{'─' * 58}{RESET}")


async def run_turn(
    triage_agent,
    session,
    user_input: str,
) -> str | None:
    """
    Run one conversation turn.

    Returns the agent's response text, or None if a guardrail blocked it.
    """
    try:
        result = await Runner.run(
            starting_agent=triage_agent,
            input=user_input,
            context=session,
        )
        return result.final_output

    except InputGuardrailTripwireTriggered as exc:
        guardrail_name = type(exc).__name__
        print(f"\n  {YELLOW}[guardrail blocked input]{RESET} {guardrail_name}")
        return (
            "I couldn't process that request. "
            "Please rephrase or ask something else."
        )

    except OutputGuardrailTripwireTriggered:
        return (
            "My response was flagged by a safety check. "
            "Try asking a more specific question."
        )


async def main() -> None:
    _print_banner()

    # Start both MCP servers as async context managers.
    # They run as subprocesses for the lifetime of the session.
    # Web search uses DuckDuckGo (Python tool, no subprocess needed).
    async with AsyncExitStack() as stack:
        fs_mcp = await stack.enter_async_context(filesystem_mcp_server())
        gh_mcp = await stack.enter_async_context(github_mcp_server())

        # Wire agents — specialists get their MCP servers, triage gets specialists
        code_review_agent  = create_code_review_agent(fs_mcp, gh_mcp, project_dir=os.getcwd())
        repo_search_agent  = create_repo_search_agent(gh_mcp, fs_mcp)
        web_research_agent = create_web_research_agent(fs_mcp)
        triage_agent       = create_triage_agent(
            code_review_agent,
            repo_search_agent,
            web_research_agent,
        )

        session = get_session()

        _print_agents_ready()

        try:
            while True:
                _print_separator()
                try:
                    user_input = input(f"{BOLD}{CYAN}You:{RESET} ").strip()
                except EOFError:
                    break

                if not user_input:
                    continue

                if user_input.lower() in {"exit", "quit", "bye"}:
                    print(f"\n  {DIM}Session saved. Goodbye!{RESET}\n")
                    break

                if user_input.lower() == "clear":
                    session = get_session(session_id=f"{config.SESSION_ID}-{id(object())}")
                    print(f"  {DIM}New session started.{RESET}")
                    continue

                print(f"\n{BOLD}DevMind:{RESET} ", end="", flush=True)
                response = await run_turn(triage_agent, session, user_input)

                if response:
                    print(response)

        except KeyboardInterrupt:
            print(f"\n\n  {DIM}Interrupted. Goodbye!{RESET}\n")


if __name__ == "__main__":
    asyncio.run(main())

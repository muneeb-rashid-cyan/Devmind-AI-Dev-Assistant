"""
Triage Agent — the entry point. Routes every user request to the right specialist.

This agent:
- Uses GPT-4o-mini for fast, cheap routing decisions
- Applies all input and output guardrails
- Hands off to Code Review, Repo Search, or Web Research agents
- Answers simple greetings and meta-questions directly

Handoff routing logic:
    file/bug/code mention   → Code Review Agent
    library/repo/GitHub     → Repo Search Agent
    error/concept/docs/web  → Web Research Agent
    greeting/meta           → answer directly
"""

from pydantic import BaseModel
from agents import Agent, handoff
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

from ..guardrails.input_guards import (
    empty_input_guardrail,
    jailbreak_guardrail,
    path_traversal_guardrail,
)
from ..guardrails.output_guards import pii_guardrail, length_guardrail
from .. import config


class HandoffReason(BaseModel):
    """Structured metadata attached to every handoff for observability."""
    reason: str          # Why the agent is handing off
    topic_summary: str   # One-sentence summary of what the user asked


def _on_code_review_handoff(context, data: HandoffReason) -> None:
    print(f"\n  [handoff → Code Review Agent] {data.reason}")
    print(f"  Topic: {data.topic_summary}")


def _on_repo_search_handoff(context, data: HandoffReason) -> None:
    print(f"\n  [handoff → Repo Search Agent] {data.reason}")
    print(f"  Topic: {data.topic_summary}")


def _on_web_research_handoff(context, data: HandoffReason) -> None:
    print(f"\n  [handoff → Web Research Agent] {data.reason}")
    print(f"  Topic: {data.topic_summary}")


TRIAGE_INSTRUCTIONS = (
    RECOMMENDED_PROMPT_PREFIX
    + """
You are DevMind, an AI-powered personal developer assistant.
Your job is to understand what the developer needs and route them to the right specialist.

=== ROUTING RULES (follow strictly) ===

→ Code Review Agent:
  - User mentions a specific file, path, or "my code"
  - Asks about bugs, errors in their OWN code
  - Wants code reviewed, explained, or improved
  - Asks "what does this function do" (about their local code)
  - Wants to compare their code to open source

→ Repo Search Agent:
  - Asks "what is the best library for..."
  - Wants to find a GitHub repo or open source project
  - Asks how a popular library implements something
  - Wants real code examples from production repos
  - Asks about npm/PyPI packages

→ Web Research Agent:
  - Gets an error message and wants a fix (general error, not their own file)
  - Asks about a concept, pattern, or best practice
  - Wants to find documentation for a tool or framework
  - Asks "how do I..." without referencing their own files
  - Asks about recent news or updates to a technology

→ Answer directly (no handoff):
  - Simple greetings: "hello", "hi", "hey"
  - Meta questions: "what can you do?", "how do you work?"
  - Very short clarifying follow-ups

=== IMPORTANT RULES ===
- NEVER answer technical questions yourself — always route to a specialist
- Always include a reason and topic_summary in your handoff
- Be friendly and brief in direct responses (1-2 sentences max)
- If unclear, ask one clarifying question before routing
"""
)


def create_triage_agent(
    code_review_agent: Agent,
    repo_search_agent: Agent,
    web_research_agent: Agent,
) -> Agent:
    """
    Create the Triage Agent wired to all three specialists.

    The specialist agents are passed in after being created with their MCP servers.
    """
    return Agent(
        name="Triage Agent",
        instructions=TRIAGE_INSTRUCTIONS,
        model=config.TRIAGE_MODEL,
        handoffs=[
            handoff(
                agent=code_review_agent,
                on_handoff=_on_code_review_handoff,
                input_type=HandoffReason,
            ),
            handoff(
                agent=repo_search_agent,
                on_handoff=_on_repo_search_handoff,
                input_type=HandoffReason,
            ),
            handoff(
                agent=web_research_agent,
                on_handoff=_on_web_research_handoff,
                input_type=HandoffReason,
            ),
        ],
        input_guardrails=[
            empty_input_guardrail,
            jailbreak_guardrail,
            path_traversal_guardrail,
        ],
        output_guardrails=[pii_guardrail, length_guardrail],
    )

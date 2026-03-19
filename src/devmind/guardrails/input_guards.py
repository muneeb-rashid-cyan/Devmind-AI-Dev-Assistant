"""
Input guardrails — fire before the Triage Agent processes the user's message.

Guards:
1. empty_input_guardrail   — rejects blank / very short inputs
2. jailbreak_guardrail     — rejects prompt injection attempts
3. path_traversal_guardrail— blocks attempts to access sensitive system paths
                             (important since agents have filesystem access)
"""

import re
from agents import (
    Agent,
    RunContextWrapper,
    TResponseInputItem,
    input_guardrail,
    GuardrailFunctionOutput,
)

# ── Pattern lists ──────────────────────────────────────────────────────────────

_INJECTION_PATTERNS = [
    "ignore previous instructions",
    "ignore all instructions",
    "disregard your instructions",
    "jailbreak",
    "dan mode",
    "developer mode",
    "act as if you have no restrictions",
]

# Sensitive paths that should never be read by the agent
_DANGEROUS_PATH_PATTERNS = [
    r"/etc/passwd",
    r"/etc/shadow",
    r"\.ssh/",
    r"\.aws/credentials",
    r"\.env$",
    r"id_rsa",
    r"/private/etc/",
    r"C:\\Windows\\System32",
    r"/proc/",
    r"/sys/",
]

_DANGEROUS_PATH_RE = re.compile(
    "|".join(_DANGEROUS_PATH_PATTERNS), re.IGNORECASE
)


def _extract_text(input: str | list[TResponseInputItem]) -> str:
    """Extract plain text from a string or list of TResponseInputItem."""
    if isinstance(input, str):
        return input

    for item in reversed(input):
        if not isinstance(item, dict):
            continue
        if item.get("role") != "user":
            continue
        content = item.get("content", "")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = [
                block.get("text", "")
                for block in content
                if isinstance(block, dict) and block.get("type") == "text"
            ]
            return " ".join(parts)

    return ""


@input_guardrail
async def empty_input_guardrail(
    context: RunContextWrapper,
    agent: Agent,
    input: str | list[TResponseInputItem],
) -> GuardrailFunctionOutput:
    """Reject empty or near-empty inputs."""
    text = _extract_text(input)
    triggered = len(text.strip()) < 3

    return GuardrailFunctionOutput(
        output_info={"reason": "Input too short or empty", "preview": text[:50]},
        tripwire_triggered=triggered,
    )


@input_guardrail
async def jailbreak_guardrail(
    context: RunContextWrapper,
    agent: Agent,
    input: str | list[TResponseInputItem],
) -> GuardrailFunctionOutput:
    """Reject inputs matching known prompt injection / jailbreak patterns."""
    text = _extract_text(input).lower()
    matched = next((p for p in _INJECTION_PATTERNS if p in text), None)

    return GuardrailFunctionOutput(
        output_info={
            "reason": f"Injection pattern matched: '{matched}'" if matched else "OK"
        },
        tripwire_triggered=matched is not None,
    )


@input_guardrail
async def path_traversal_guardrail(
    context: RunContextWrapper,
    agent: Agent,
    input: str | list[TResponseInputItem],
) -> GuardrailFunctionOutput:
    """
    Block requests that try to read sensitive system files.

    This matters because the Code Review Agent has filesystem access.
    Without this guard, a user could ask "read /etc/passwd" and the
    agent would happily do it.
    """
    text = _extract_text(input)
    matched = _DANGEROUS_PATH_RE.search(text)

    return GuardrailFunctionOutput(
        output_info={
            "reason": f"Dangerous path detected: '{matched.group()}'" if matched else "OK"
        },
        tripwire_triggered=matched is not None,
    )

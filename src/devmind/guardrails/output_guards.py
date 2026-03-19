"""
Output guardrails — fire after an agent responds.

Guards:
1. length_guardrail  — flags responses that exceed the character limit
2. pii_guardrail     — detects accidental PII (email, phone, API keys) in output
"""

import re
from agents import (
    Agent,
    RunContextWrapper,
    output_guardrail,
    GuardrailFunctionOutput,
)
from .. import config


# ── Regex patterns ─────────────────────────────────────────────────────────────
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
_PHONE_RE = re.compile(r"\b(\+?\d[\d\s\-().]{7,}\d)\b")
# Detects what looks like API keys / tokens (long alphanumeric strings with hyphens/underscores)
_API_KEY_RE = re.compile(r"\b(sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{36}|BSA[A-Za-z0-9]{30,})\b")


@output_guardrail
async def length_guardrail(
    context: RunContextWrapper,
    agent: Agent,
    output: str,
) -> GuardrailFunctionOutput:
    """Flag responses that exceed the maximum character limit."""
    triggered = len(output) > config.MAX_RESPONSE_CHARS

    return GuardrailFunctionOutput(
        output_info={
            "reason": (
                f"Response too long ({len(output)} chars > {config.MAX_RESPONSE_CHARS})"
                if triggered
                else "OK"
            ),
            "preview": output[:80],
        },
        tripwire_triggered=triggered,
    )


@output_guardrail
async def pii_guardrail(
    context: RunContextWrapper,
    agent: Agent,
    output: str,
) -> GuardrailFunctionOutput:
    """
    Detect accidental PII or secrets in agent output.

    Catches:
    - Email addresses
    - Phone numbers
    - API keys / tokens (OpenAI sk-, GitHub ghp_, Brave BSA...)
    """
    has_email = bool(_EMAIL_RE.search(output))
    has_phone = bool(_PHONE_RE.search(output))
    has_key = bool(_API_KEY_RE.search(output))
    triggered = has_email or has_phone or has_key

    return GuardrailFunctionOutput(
        output_info={
            "reason": "PII or secrets detected" if triggered else "OK",
            "has_email": has_email,
            "has_phone": has_phone,
            "has_api_key": has_key,
        },
        tripwire_triggered=triggered,
    )

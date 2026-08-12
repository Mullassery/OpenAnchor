"""Privacy/redaction utilities for captured LLM prompt & response content.

OpenAnchor's entire job is intercepting and storing metadata about LLM
calls. Some integrations (e.g. ``middleware/langchain.py``) can also
capture excerpts of the actual prompt/response text, which may contain
PII, secrets, or otherwise sensitive content. This module centralizes the
safe-by-default handling of that content:

- Raw content capture is **off by default**. Callers must opt in.
- When raw content capture is enabled, a best-effort PII/secret redaction
  pass runs over the excerpt by default (also toggleable).
- Either way, a content hash + length is always recorded, so it's
  possible to notice "this call repeated the same prompt" or measure
  prompt sizes without ever persisting the raw text.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Dict

# Best-effort PII/secret patterns. Not exhaustive — this is a pragmatic
# safety net, not a compliance guarantee. Order matters: more specific
# patterns (API keys) before more general ones (long digit runs).
_PATTERNS = [
    ("email", re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")),
    ("api_key", re.compile(r"\b(?:sk|pk|rk|api)-[A-Za-z0-9_-]{16,}\b")),
    ("bearer_token", re.compile(r"\bBearer\s+[A-Za-z0-9_\-.]{16,}\b", re.IGNORECASE)),
    ("credit_card", re.compile(r"\b(?:\d[ -]?){13,16}\b")),
    ("ssn", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("phone", re.compile(r"\b(?:\+?\d{1,2}[ .-]?)?\(?\d{3}\)?[ .-]?\d{3}[ .-]?\d{4}\b")),
    ("ipv4", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
]


def redact_pii(text: str) -> str:
    """Best-effort redaction of common PII/secret patterns in ``text``."""
    if not text:
        return text
    redacted = text
    for label, pattern in _PATTERNS:
        redacted = pattern.sub(f"<REDACTED_{label.upper()}>", redacted)
    return redacted


def hash_content(text: str) -> str:
    """SHA-256 hex digest of ``text`` (for dedup/repeat-detection without storing it)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def summarize_captured_content(
    text: Any,
    *,
    capture_raw: bool = False,
    redact: bool = True,
    max_chars: int = 500,
) -> Dict[str, Any]:
    """Build the dict that gets persisted for a piece of captured content.

    Args:
        text: The raw value to summarize (coerced to ``str``).
        capture_raw: If False (the safe default), no excerpt of the raw
            text is stored at all — only a hash + length. If True, an
            (optionally redacted) excerpt up to ``max_chars`` is included.
        redact: When ``capture_raw`` is True, whether to run
            ``redact_pii`` over the excerpt before storing it. Defaults to
            True — even opt-in raw capture gets a safety net unless a
            caller explicitly turns it off.
        max_chars: Maximum excerpt length when ``capture_raw`` is True.

    Returns:
        A dict safe to store in ``TokenEvent.request_data``/``response_data``:
        always includes ``content_sha256`` and ``content_length``; includes
        ``excerpt`` and ``redacted`` only when ``capture_raw`` is True.
    """
    text_str = "" if text is None else str(text)

    summary: Dict[str, Any] = {
        "content_sha256": hash_content(text_str),
        "content_length": len(text_str),
        "captured": bool(capture_raw),
    }

    if capture_raw:
        excerpt = text_str[:max_chars]
        if redact:
            excerpt = redact_pii(excerpt)
        summary["excerpt"] = excerpt
        summary["redacted"] = redact

    return summary

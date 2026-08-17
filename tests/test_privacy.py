"""Tests for openanchor/privacy.py (redaction/retention BLOCKER fix)."""

from openanchor.privacy import hash_content, redact_pii, summarize_captured_content


class TestRedactPii:
    def test_redacts_email(self):
        assert "user@example.com" not in redact_pii("Contact me at user@example.com please")
        assert "<REDACTED_EMAIL>" in redact_pii("Contact me at user@example.com please")

    def test_redacts_api_key(self):
        text = "Use sk-abcdef1234567890ABCDEF for auth"
        redacted = redact_pii(text)
        assert "sk-abcdef1234567890ABCDEF" not in redacted
        assert "<REDACTED_API_KEY>" in redacted

    def test_redacts_ssn(self):
        assert "<REDACTED_SSN>" in redact_pii("SSN: 123-45-6789")

    def test_redacts_phone(self):
        redacted = redact_pii("Call me at 555-123-4567")
        assert "555-123-4567" not in redacted

    def test_leaves_ordinary_text_alone(self):
        text = "The quick brown fox jumps over the lazy dog."
        assert redact_pii(text) == text

    def test_empty_string(self):
        assert redact_pii("") == ""


class TestHashContent:
    def test_deterministic(self):
        assert hash_content("hello") == hash_content("hello")

    def test_different_text_different_hash(self):
        assert hash_content("hello") != hash_content("world")

    def test_is_sha256_hex(self):
        digest = hash_content("hello")
        assert len(digest) == 64
        int(digest, 16)  # raises if not valid hex


class TestSummarizeCapturedContent:
    def test_default_does_not_capture_raw_text(self):
        summary = summarize_captured_content("my secret prompt: email me at a@b.com")
        assert "excerpt" not in summary
        assert "redacted" not in summary
        assert summary["captured"] is False
        assert summary["content_length"] == len("my secret prompt: email me at a@b.com")
        assert summary["content_sha256"] == hash_content(
            "my secret prompt: email me at a@b.com"
        )

    def test_opt_in_capture_includes_redacted_excerpt(self):
        summary = summarize_captured_content(
            "email me at a@b.com", capture_raw=True, redact=True
        )
        assert summary["captured"] is True
        assert summary["redacted"] is True
        assert "a@b.com" not in summary["excerpt"]

    def test_opt_in_capture_without_redaction(self):
        summary = summarize_captured_content(
            "email me at a@b.com", capture_raw=True, redact=False
        )
        assert summary["redacted"] is False
        assert "a@b.com" in summary["excerpt"]

    def test_excerpt_respects_max_chars(self):
        summary = summarize_captured_content(
            "x" * 1000, capture_raw=True, max_chars=50
        )
        assert len(summary["excerpt"]) == 50

    def test_non_string_input_is_coerced(self):
        summary = summarize_captured_content(12345, capture_raw=True)
        assert summary["excerpt"] == "12345"
        assert summary["content_length"] == 5

    def test_none_input_treated_as_empty(self):
        summary = summarize_captured_content(None)
        assert summary["content_length"] == 0

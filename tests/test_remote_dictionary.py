import json
import unicodedata
import urllib.error

import pytest

from server.remote_dictionary import RemoteDictionary
from tests.conftest import (
    ENGLISH_HELLO,
    KNOWN_LANG,
    KNOWN_WORD,
    UNKNOWN_LANG,
    UNKNOWN_WORD,
    DictionaryProviderTests,
)


class _MockResponse:
    """Minimal context-manager response for urllib.request.urlopen."""

    def __init__(self, data: dict):
        self._bytes = json.dumps(data).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self) -> bytes:
        return self._bytes


def _make_urlopen(responses: dict, default_error: bool = True):
    """Return a fake urlopen that maps URL substrings to response dicts.

    If no key matches and default_error is True, raises HTTP 404.
    """
    def fake_urlopen(url):
        for key, data in responses.items():
            if key in url:
                return _MockResponse(data)
        if default_error:
            raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)
        return _MockResponse({"entries": []})

    return fake_urlopen


class TestRemoteDictionary(DictionaryProviderTests):
    @pytest.fixture
    def provider(self, monkeypatch):
        """RemoteDictionary with urlopen mocked.

        Returns ENGLISH_HELLO for KNOWN_WORD/KNOWN_LANG; raises HTTP 404 for
        everything else (so UNKNOWN_WORD lookups correctly return []).
        """
        monkeypatch.setattr(
            "urllib.request.urlopen",
            _make_urlopen({KNOWN_WORD: {"entries": [ENGLISH_HELLO]}}),
        )
        return RemoteDictionary()

    def test_http_error_returns_empty_list(self, monkeypatch):
        def raise_404(url):
            raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)

        monkeypatch.setattr("urllib.request.urlopen", raise_404)
        assert RemoteDictionary().lookup("nonexistent", "en") == []

    def test_missing_entries_key_returns_empty_list(self, monkeypatch):
        monkeypatch.setattr(
            "urllib.request.urlopen",
            lambda url: _MockResponse({"other_key": []}),
        )
        assert RemoteDictionary().lookup("hello", "en") == []

    def test_url_contains_word_and_lang(self, monkeypatch):
        captured = []

        def fake_urlopen(url):
            captured.append(url)
            return _MockResponse({"entries": []})

        monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
        RemoteDictionary().lookup("hello", "en")
        assert len(captured) == 1
        assert "hello" in captured[0]
        assert "en" in captured[0]

    def test_url_percent_encodes_special_characters(self, monkeypatch):
        captured = []

        def fake_urlopen(url):
            captured.append(url)
            return _MockResponse({"entries": []})

        monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
        RemoteDictionary().lookup("café", "fr")
        assert "caf%C3%A9" in captured[0]

    def test_unicode_input_normalized_before_encoding(self, monkeypatch):
        """NFD input is normalized to NFC, then URL-encoded the same as NFC input."""
        captured_nfc = []
        captured_nfd = []

        def capture_nfc(url):
            captured_nfc.append(url)
            return _MockResponse({"entries": []})

        def capture_nfd(url):
            captured_nfd.append(url)
            return _MockResponse({"entries": []})

        nfc = unicodedata.normalize("NFC", "café")
        nfd = unicodedata.normalize("NFD", "café")

        monkeypatch.setattr("urllib.request.urlopen", capture_nfc)
        RemoteDictionary().lookup(nfc, "fr")

        monkeypatch.setattr("urllib.request.urlopen", capture_nfd)
        RemoteDictionary().lookup(nfd, "fr")

        assert captured_nfc[0] == captured_nfd[0]

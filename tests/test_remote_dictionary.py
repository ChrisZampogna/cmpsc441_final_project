import json
import unicodedata
import urllib.error
import urllib.request

import pytest

from server.remote_dictionary import RemoteDictionary
from tests.conftest import (
    ENGLISH_HELLO,
    KNOWN_LANG,
    KNOWN_WORD,
    DictionaryProviderTests,
)

_KNOWN_DEFINITION = {"pos": "intj", "lang_code": KNOWN_LANG, "senses": ENGLISH_HELLO.get("senses", [])}


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


def _url(req) -> str:
    """Extract the URL string from either a Request object or a plain string."""
    return req.full_url if isinstance(req, urllib.request.Request) else req


def _make_urlopen(responses: list[tuple[str, dict]], default_error: bool = True):
    """Return a fake urlopen matching URLs against an ordered list of (substring, response) pairs.

    The first matching substring wins, so put more-specific keys earlier.
    If nothing matches and default_error is True, raises HTTP 404.
    """
    def fake_urlopen(req):
        url = _url(req)
        for key, data in responses:
            if key in url:
                return _MockResponse(data)
        if default_error:
            raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)
        return _MockResponse({})

    return fake_urlopen


class TestRemoteDictionary(DictionaryProviderTests):
    @pytest.fixture
    def provider(self, monkeypatch):
        """RemoteDictionary with both endpoints mocked.

        KNOWN_WORD/KNOWN_LANG returns ENGLISH_HELLO from the word endpoint and
        a matching definition (with pos) from the definitions endpoint.
        All other lookups raise HTTP 404 so unknown-word tests return [].
        """
        monkeypatch.setattr(
            "urllib.request.urlopen",
            _make_urlopen([
                ("/definitions", {"definitions": [_KNOWN_DEFINITION]}),
                (KNOWN_WORD,     {"entries": [ENGLISH_HELLO]}),
            ]),
        )
        return RemoteDictionary()

    def test_pos_merged_from_definitions_endpoint(self, monkeypatch):
        entry = {"senses": [{"glosses": ["a greeting"]}]}
        defn  = {"pos": "interjection", "lang_code": "en", "senses": []}
        monkeypatch.setattr(
            "urllib.request.urlopen",
            _make_urlopen([
                ("/definitions", {"definitions": [defn]}),
                ("hello",        {"entries": [entry]}),
            ]),
        )
        result = RemoteDictionary().lookup("hello", "en")
        assert result[0]["pos"] == "interjection"

    def test_http_error_returns_empty_list(self, monkeypatch):
        def raise_404(req):
            raise urllib.error.HTTPError(_url(req), 404, "Not Found", {}, None)

        monkeypatch.setattr("urllib.request.urlopen", raise_404)
        assert RemoteDictionary().lookup("nonexistent", "en") == []

    def test_missing_entries_key_returns_empty_list(self, monkeypatch):
        monkeypatch.setattr(
            "urllib.request.urlopen",
            lambda req: _MockResponse({}),
        )
        assert RemoteDictionary().lookup("hello", "en") == []

    def test_two_requests_made_per_lookup(self, monkeypatch):
        captured = []

        def fake_urlopen(req):
            captured.append(_url(req))
            return _MockResponse({})

        monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
        RemoteDictionary().lookup("hello", "en")
        assert len(captured) == 2

    def test_urls_contain_word_and_lang(self, monkeypatch):
        captured = []

        def fake_urlopen(req):
            captured.append(_url(req))
            return _MockResponse({})

        monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
        RemoteDictionary().lookup("hello", "en")
        assert all("hello" in u and "en" in u for u in captured)

    def test_definitions_url_uses_definitions_endpoint(self, monkeypatch):
        captured = []

        def fake_urlopen(req):
            captured.append(_url(req))
            return _MockResponse({})

        monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
        RemoteDictionary().lookup("hello", "en")
        assert any("/definitions" in u for u in captured)

    def test_url_percent_encodes_special_characters(self, monkeypatch):
        captured = []

        def fake_urlopen(req):
            captured.append(_url(req))
            return _MockResponse({})

        monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
        RemoteDictionary().lookup("café", "fr")
        assert all("caf%C3%A9" in u for u in captured)

    def test_unicode_input_normalized_before_encoding(self, monkeypatch):
        """NFD input is normalized to NFC, then URL-encoded the same as NFC input."""
        captured_nfc = []
        captured_nfd = []

        def capture_nfc(req):
            captured_nfc.append(_url(req))
            return _MockResponse({})

        def capture_nfd(req):
            captured_nfd.append(_url(req))
            return _MockResponse({})

        nfc = unicodedata.normalize("NFC", "café")
        nfd = unicodedata.normalize("NFD", "café")

        monkeypatch.setattr("urllib.request.urlopen", capture_nfc)
        RemoteDictionary().lookup(nfc, "fr")

        monkeypatch.setattr("urllib.request.urlopen", capture_nfd)
        RemoteDictionary().lookup(nfd, "fr")

        assert captured_nfc == captured_nfd

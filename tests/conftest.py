"""Shared test data and base test class for DictionaryProvider implementations."""

import pytest

ENGLISH_HELLO = {
    "word": "hello",
    "lang_code": "en",
    "pos": "intj",
    "senses": [{"glosses": ["Used to greet someone."]}],
}
KNOWN_WORD = "hello"
KNOWN_LANG = "en"
UNKNOWN_WORD = "zzz_notaword_xyz"
UNKNOWN_LANG = "en"


class DictionaryProviderTests:
    """Shared tests run against every DictionaryProvider implementation.

    Subclasses must override the ``provider`` fixture to return an instance
    pre-loaded (or mocked) so that ``(KNOWN_WORD, KNOWN_LANG)`` returns at
    least ``ENGLISH_HELLO`` and ``(UNKNOWN_WORD, UNKNOWN_LANG)`` returns ``[]``.
    """

    @pytest.fixture
    def provider(self):
        raise NotImplementedError

    def test_lookup_returns_list(self, provider):
        result = provider.lookup(KNOWN_WORD, KNOWN_LANG)
        assert isinstance(result, list)

    def test_lookup_known_word_returns_at_least_one_entry(self, provider):
        result = provider.lookup(KNOWN_WORD, KNOWN_LANG)
        assert len(result) >= 1

    def test_lookup_entries_are_dicts(self, provider):
        result = provider.lookup(KNOWN_WORD, KNOWN_LANG)
        assert all(isinstance(entry, dict) for entry in result)

    def test_lookup_unknown_word_returns_empty_list(self, provider):
        result = provider.lookup(UNKNOWN_WORD, UNKNOWN_LANG)
        assert result == []

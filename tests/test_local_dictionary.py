import json
import sqlite3
import unicodedata

import pytest

from server.local_dictionary import LocalDictionary
from tests.conftest import (
    ENGLISH_HELLO,
    KNOWN_LANG,
    KNOWN_WORD,
    DictionaryProviderTests,
)


def _make_db(tmp_path, rows: list[tuple]) -> LocalDictionary:
    """Create a temporary SQLite DB, insert rows, return a LocalDictionary."""
    db_path = tmp_path / "test.db"
    con = sqlite3.connect(db_path)
    con.execute("CREATE TABLE entries (word TEXT, lang_code TEXT, pos TEXT, raw TEXT)")
    con.executemany("INSERT INTO entries VALUES (?, ?, ?, ?)", rows)
    con.commit()
    con.close()
    return LocalDictionary(db_path)


class TestLocalDictionary(DictionaryProviderTests):
    @pytest.fixture
    def provider(self, tmp_path):
        return _make_db(
            tmp_path,
            [(KNOWN_WORD, KNOWN_LANG, ENGLISH_HELLO["pos"], json.dumps(ENGLISH_HELLO))],
        )

    def test_lookup_returns_parsed_json(self, provider):
        result = provider.lookup(KNOWN_WORD, KNOWN_LANG)
        assert result[0]["word"] == KNOWN_WORD

    def test_lookup_multiple_rows_same_word_all_returned(self, tmp_path):
        entry2 = dict(ENGLISH_HELLO, pos="noun")
        provider = _make_db(
            tmp_path,
            [
                (KNOWN_WORD, KNOWN_LANG, "intj", json.dumps(ENGLISH_HELLO)),
                (KNOWN_WORD, KNOWN_LANG, "noun", json.dumps(entry2)),
            ],
        )
        assert len(provider.lookup(KNOWN_WORD, KNOWN_LANG)) == 2

    def test_lookup_wrong_lang_returns_empty(self, provider):
        assert provider.lookup(KNOWN_WORD, "fr") == []

    def test_lookup_normalizes_unicode_input(self, tmp_path):
        """NFD-encoded query finds an NFC-stored word."""
        nfc = unicodedata.normalize("NFC", "café")
        nfd = unicodedata.normalize("NFD", "café")
        entry = {"word": nfc, "lang_code": "fr", "pos": "noun"}
        provider = _make_db(tmp_path, [(nfc, "fr", "noun", json.dumps(entry))])

        result = provider.lookup(nfd, "fr")
        assert len(result) == 1
        assert result[0]["word"] == nfc


class TestDescribe:
    """Tests for DictionaryProvider.describe(), the concrete template method."""

    RICH_ENTRY = {
        "word": "chat",
        "lang_code": "fr",
        "pos": "noun",
        "etymology_text": "From Latin cattus.",
        "senses": [
            {
                "glosses": ["cat (feline)"],
                "tags": ["masculine"],
                "examples": [
                    {"text": "Le chat dort.", "english": "The cat sleeps."}
                ],
            },
            {
                "glosses": ["tomcat"],
                "tags": ["masculine"],
            },
        ],
        "sounds": [{"ipa": "/ʃa/"}, {"audio": "Fr-chat.ogg"}],
        "forms": [
            {"form": "chats", "tags": ["plural"]},
            {"form": "chatte", "tags": ["feminine"]},
        ],
    }

    @pytest.fixture
    def provider(self, tmp_path):
        return _make_db(
            tmp_path,
            [("chat", "fr", "noun", json.dumps(self.RICH_ENTRY))],
        )

    def test_describe_returns_list(self, provider):
        assert isinstance(provider.describe("chat", "fr"), list)

    def test_describe_unknown_word_returns_empty(self, provider):
        assert provider.describe("zzz_notaword", "fr") == []

    def test_describe_extracts_pos(self, provider):
        result = provider.describe("chat", "fr")
        assert result[0]["pos"] == "noun"

    def test_describe_extracts_etymology(self, provider):
        result = provider.describe("chat", "fr")
        assert result[0]["etymology"] == "From Latin cattus."

    def test_describe_extracts_ipa_only(self, provider):
        """Non-IPA sound entries (audio files) are excluded."""
        result = provider.describe("chat", "fr")
        assert result[0]["ipa"] == ["/ʃa/"]

    def test_describe_extracts_forms(self, provider):
        result = provider.describe("chat", "fr")
        forms = result[0]["forms"]
        assert {"form": "chats", "tags": ["plural"]} in forms
        assert {"form": "chatte", "tags": ["feminine"]} in forms

    def test_describe_extracts_glosses(self, provider):
        result = provider.describe("chat", "fr")
        senses = result[0]["senses"]
        assert senses[0]["glosses"] == ["cat (feline)"]

    def test_describe_extracts_tags(self, provider):
        result = provider.describe("chat", "fr")
        assert result[0]["senses"][0]["tags"] == ["masculine"]

    def test_describe_extracts_example(self, provider):
        result = provider.describe("chat", "fr")
        sense = result[0]["senses"][0]
        assert sense["example"] == "Le chat dort."
        assert sense["example_translation"] == "The cat sleeps."

    def test_describe_sense_without_example_omits_key(self, provider):
        result = provider.describe("chat", "fr")
        sense = result[0]["senses"][1]
        assert "example" not in sense

    def test_describe_entry_without_etymology_omits_key(self, tmp_path):
        entry = dict(self.RICH_ENTRY)
        del entry["etymology_text"]
        provider = _make_db(tmp_path, [("chat", "fr", "noun", json.dumps(entry))])
        result = provider.describe("chat", "fr")
        assert "etymology" not in result[0]

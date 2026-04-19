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

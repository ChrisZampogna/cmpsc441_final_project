import json
import sqlite3
import unicodedata
from pathlib import Path

from server.dictionary_provider import DictionaryProvider

DB_PATH = Path("data/generated/wiktionary.db")

class LocalDictionary(DictionaryProvider):
    def __init__(self, db_path: Path = DB_PATH) -> None:
        self._db_path = db_path
        self._con = sqlite3.connect(db_path)

    def lookup(self, word: str, lang_code: str) -> list[dict]:
        word = unicodedata.normalize("NFC", word)
        lang_code = unicodedata.normalize("NFC", lang_code)
        rows = self._con.execute(
            "SELECT raw FROM entries WHERE word = ? AND lang_code = ?",
            (word, lang_code),
        ).fetchall()
        return [json.loads(row[0]) for row in rows]

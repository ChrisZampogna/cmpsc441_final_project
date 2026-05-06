import sqlite3
import unicodedata
from pathlib import Path

VOCAB_DB_PATH = Path("data/vocab.db")


class VocabStore:
    def __init__(self, db_path: Path = VOCAB_DB_PATH) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._con = sqlite3.connect(db_path, check_same_thread=False)
        self._con.execute("""
            CREATE TABLE IF NOT EXISTS vocab_words (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                word      TEXT NOT NULL,
                lang_code TEXT NOT NULL,
                added_at  TEXT DEFAULT (datetime('now')),
                UNIQUE(word, lang_code)
            )
        """)
        self._con.commit()

    @staticmethod
    def _normalize(text: str) -> str:
        return unicodedata.normalize("NFC", text)

    def add_word(self, word: str, lang_code: str) -> bool:
        word = self._normalize(word)
        lang_code = self._normalize(lang_code)
        try:
            self._con.execute(
                "INSERT INTO vocab_words (word, lang_code) VALUES (?, ?)",
                (word, lang_code),
            )
            self._con.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def add_words(self, words: list[str], lang_code: str) -> tuple[int, int]:
        added = 0
        skipped = 0
        for word in words:
            if self.add_word(word, lang_code):
                added += 1
            else:
                skipped += 1
        return added, skipped

    def remove_word(self, word: str, lang_code: str) -> bool:
        word = self._normalize(word)
        lang_code = self._normalize(lang_code)
        cursor = self._con.execute(
            "DELETE FROM vocab_words WHERE word = ? AND lang_code = ?",
            (word, lang_code),
        )
        self._con.commit()
        return cursor.rowcount > 0

    def list_words(self, lang_code: str) -> list[str]:
        lang_code = self._normalize(lang_code)
        rows = self._con.execute(
            "SELECT word FROM vocab_words WHERE lang_code = ? ORDER BY word ASC",
            (lang_code,),
        ).fetchall()
        return [row[0] for row in rows]

    def clear_words(self, lang_code: str) -> int:
        lang_code = self._normalize(lang_code)
        cursor = self._con.execute(
            "DELETE FROM vocab_words WHERE lang_code = ?",
            (lang_code,),
        )
        self._con.commit()
        return cursor.rowcount

    def word_exists(self, word: str, lang_code: str) -> bool:
        word = self._normalize(word)
        lang_code = self._normalize(lang_code)
        row = self._con.execute(
            "SELECT 1 FROM vocab_words WHERE word = ? AND lang_code = ?",
            (word, lang_code),
        ).fetchone()
        return row is not None

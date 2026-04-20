import json
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

from server.dictionary_provider import DictionaryProvider

_BASE_URL = "https://api.wiktapi.dev/v1/en/word"


class RemoteDictionary(DictionaryProvider):
    def _fetch(self, url: str) -> dict:
        req = urllib.request.Request(url, headers={"User-Agent": "cmpsc441-final-project-language-assistant/0.1"})
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            print(e, file=sys.stderr)
            return {}

    def lookup(self, word: str, lang_code: str) -> list[dict]:
        word = unicodedata.normalize("NFC", word)
        lang_code = unicodedata.normalize("NFC", lang_code)
        quoted_word = urllib.parse.quote(word, safe="")
        quoted_lang = urllib.parse.quote(lang_code, safe="")

        entries = self._fetch(
            f"{_BASE_URL}/{quoted_word}?lang={quoted_lang}"
        ).get("entries", [])

        definitions = self._fetch(
            f"{_BASE_URL}/{quoted_word}/definitions?lang={quoted_lang}"
        ).get("definitions", [])

        for entry, defn in zip(entries, definitions):
            entry["pos"] = defn.get("pos", "")

        return entries

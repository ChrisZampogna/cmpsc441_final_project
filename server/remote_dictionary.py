import json
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

from server.dictionary_provider import DictionaryProvider

BASE_URL = "https://api.wiktapi.dev/v1/en/word"

class RemoteDictionary(DictionaryProvider):
    def lookup(self, word: str, lang_code: str) -> list[dict]:
        word = unicodedata.normalize("NFC", word)
        lang_code = unicodedata.normalize("NFC", lang_code)
        url = f"{BASE_URL}/{urllib.parse.quote(word, safe='')}?lang={urllib.parse.quote(lang_code, safe='')}"
        try:
            with urllib.request.urlopen(url) as resp:
                data = json.loads(resp.read().decode())
        except urllib.error.HTTPError:
            return []
        return data.get("entries", [])

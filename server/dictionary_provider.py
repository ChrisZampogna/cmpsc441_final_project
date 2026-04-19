from abc import ABC, abstractmethod

class DictionaryProvider(ABC):
    @abstractmethod
    def lookup(self, word: str, lang_code: str) -> list[dict]:
        ...

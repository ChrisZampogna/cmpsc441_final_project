from abc import ABC, abstractmethod


class DictionaryProvider(ABC):
    @abstractmethod
    def lookup(self, word: str, lang_code: str) -> list[dict]:
        ...

    def describe(self, word: str, lang_code: str) -> list[dict]:
        """Return a list of structured summaries, one per entry.

        Each summary contains the fields most useful to a language learner:
        part of speech, etymology, senses (with glosses, tags, and an example),
        IPA pronunciations, and inflected forms. All fields are extracted with
        safe .get() calls so missing data is silently omitted.
        """
        entries = self.lookup(word, lang_code)
        results = []
        for entry in entries:
            ipa = [
                s["ipa"]
                for s in entry.get("sounds", [])
                if "ipa" in s
            ]
            forms = [
                {"form": f["form"], "tags": f.get("tags", [])}
                for f in entry.get("forms", [])
                if f.get("form")
            ]
            senses = []
            for sense in entry.get("senses", []):
                sense_info: dict = {"glosses": sense.get("glosses", [])}
                tags = sense.get("tags", [])
                if tags:
                    sense_info["tags"] = tags
                examples = sense.get("examples", [])
                if examples:
                    ex = examples[0]
                    sense_info["example"] = ex.get("text", "")
                    translation = ex.get("english") or ex.get("translation")
                    if translation:
                        sense_info["example_translation"] = translation
                senses.append(sense_info)

            summary: dict = {
                "pos": entry.get("pos", ""),
                "senses": senses,
            }
            if ipa:
                summary["ipa"] = ipa
            if forms:
                summary["forms"] = forms
            etymology = entry.get("etymology_text", "")
            if etymology:
                summary["etymology"] = etymology

            results.append(summary)
        return results

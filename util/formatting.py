import json


def format_dict(obj: dict) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False)


def format_list(string_list: list[str]) -> str:
    prefixed = ["- " + item for item in string_list]
    return "\n".join(prefixed)


def format_word_details(word: str, lang_code: str, entries: list[dict]) -> str:
    """Format the output of DictionaryProvider.describe() into a readable string."""
    if not entries:
        return f"No entries found for '{word}' ({lang_code})."

    lines = [f"# {word} ({lang_code.upper()})"]
    for i, entry in enumerate(entries, 1):
        if len(entries) > 1:
            lines.append(f"\n## Entry {i}")

        pos = entry.get("pos", "")
        if pos:
            lines.append(f"**Part of speech:** {pos}")

        etymology = entry.get("etymology", "")
        if etymology:
            lines.append(f"**Etymology:** {etymology}")

        ipa = entry.get("ipa", [])
        if ipa:
            lines.append(f"**Pronunciation:** {', '.join(ipa)}")

        forms = entry.get("forms", [])
        if forms:
            form_strs = [
                f"{f['form']} ({', '.join(f['tags'])})" if f.get("tags") else f["form"]
                for f in forms
            ]
            lines.append(f"**Forms:** {', '.join(form_strs)}")

        senses = entry.get("senses", [])
        if senses:
            lines.append("**Senses:**")
            for sense in senses:
                glosses = sense.get("glosses", [])
                tags = sense.get("tags", [])
                gloss_str = "; ".join(glosses)
                tag_str = f" [{', '.join(tags)}]" if tags else ""
                lines.append(f"  - {gloss_str}{tag_str}")
                example = sense.get("example", "")
                if example:
                    lines.append(f'    *"{example}"*')
                    translation = sense.get("example_translation", "")
                    if translation:
                        lines.append(f'    *"{translation}"*')

    return "\n".join(lines)

import random

from fastmcp import FastMCP

from server.local_dictionary import LocalDictionary
from server.remote_dictionary import RemoteDictionary
from server.dictionary_provider import DictionaryProvider
from server.enum.tool_status import ToolStatus
from server.rag_provider import RagProvider
from server.vocab_store import VocabStore
from util.formatting import format_list, format_word_details
from util.config import load_config

mcp = FastMCP("dictionary")

config = load_config()
match config.get("dictionaryProvider", "local"):
    case "remote":
        dictionary: DictionaryProvider = RemoteDictionary()
    case "local":
        dictionary: DictionaryProvider = LocalDictionary()
    case other:
        raise ValueError(f"Unknown dictionaryProvider: {other}")

vocab_store = VocabStore()

_rag: RagProvider | None = None

def get_rag() -> RagProvider:
    global _rag
    if _rag is None:
        _rag = RagProvider(config)
    return _rag

@mcp.tool()
def get_definitions(word: str, lang_code: str) -> str:
    """
    Look up definitions of a word in a given language
    May return many results for the many senses of a word
    Each definition will be printed on a new line
    Example inputs:
        get_definitions("hello", "en")
        get_definitions("chat", "fr")
    """
    result = dictionary.lookup(word, lang_code.lower())
    glosses = [
        gloss
        for entry in result
        for sense in entry.get("senses", [])
        for gloss in sense.get("glosses", [])
    ]
    return format_list(glosses)

@mcp.tool()
def get_word_details(word: str, lang_code: str) -> str:
    """
    Look up rich metadata for a word in a given language.
    Returns part of speech, etymology, pronunciation (IPA), inflected forms,
    and definitions with usage examples.
    Use this when the user wants more than just a definition.
    Example inputs:
        get_word_details("chat", "fr")
        get_word_details("run", "en")
    """
    entries = dictionary.describe(word, lang_code)
    return format_word_details(word, lang_code, entries)

@mcp.tool()
def search_books(query: str) -> str:
    """
    Search the Spanish language textbooks for information relevant to a grammar
    or vocabulary question. Returns the most relevant passages from:
    - Libro Libre (Spanish textbook)
    - Spanish Grammar Manual
    Use this when the user asks grammar questions or wants explanations of
    Spanish language rules.
    Example inputs:
        search_books("subjunctive mood usage")
        search_books("ser vs estar difference")
        search_books("preterite vs imperfect")
    """
    return get_rag().search(query)

@mcp.tool()
def add_vocab_word(word: str, lang_code: str) -> str:
    """
    Add a single word to the user's vocabulary list for a given language.
    Example inputs:
        add_vocab_word("hola", "es")
        add_vocab_word("bonjour", "fr")
    """
    added = vocab_store.add_word(word, lang_code)
    if added:
        return f"{ToolStatus.SUCCESS}: '{word}' was added to the {lang_code} vocabulary list."
    return f"{ToolStatus.DUPLICATE}: '{word}' is already in the {lang_code} vocabulary list. No action needed."


@mcp.tool()
def add_vocab_words(words: list[str], lang_code: str) -> str:
    """
    Add multiple words to the user's vocabulary list for a given language.
    Use this to bulk-add a category of words (e.g. foods, colors, verbs).
    Example inputs:
        add_vocab_words(["manzana", "pollo", "arroz"], "es")
        add_vocab_words(["rouge", "bleu", "vert"], "fr")
    """
    added, skipped = vocab_store.add_words(words, lang_code)
    parts = [f"{ToolStatus.SUCCESS}: Added {added} word(s) to the {lang_code} vocabulary list."]
    if skipped:
        parts.append(f"{skipped} duplicate(s) were already present and skipped.")
    return " ".join(parts)


@mcp.tool()
def remove_vocab_word(word: str, lang_code: str) -> str:
    """
    Remove a word from the user's vocabulary list for a given language.
    Example inputs:
        remove_vocab_word("hola", "es")
        remove_vocab_word("bonjour", "fr")
    """
    removed = vocab_store.remove_word(word, lang_code)
    if removed:
        return f"{ToolStatus.SUCCESS}: '{word}' was removed from the {lang_code} vocabulary list."
    return f"{ToolStatus.NOT_FOUND}: '{word}' was not in the {lang_code} vocabulary list. No action taken."


@mcp.tool()
def list_vocab_words(lang_code: str) -> str:
    """
    List all vocabulary words saved for a given language.
    If the user does not specify a language, ask them which language before calling this tool.
    Do not guess the language or call this tool multiple times for different languages.
    Example inputs:
        list_vocab_words("es")
        list_vocab_words("fr")
    """
    words = vocab_store.list_words(lang_code)
    if not words:
        return f"{ToolStatus.SUCCESS}: The {lang_code} vocabulary list is empty (no words added yet)."
    return f"{ToolStatus.SUCCESS}: Found {len(words)} word(s) in the {lang_code} vocabulary list:\n" + format_list(words)


@mcp.tool()
def clear_vocab_list(lang_code: str) -> str:
    """
    Remove all vocabulary words for a given language.
    If the user does not specify a language, ask them which language before calling this tool.
    Example inputs:
        clear_vocab_list("es")
        clear_vocab_list("fr")
    """
    count = vocab_store.clear_words(lang_code)
    return f"{ToolStatus.SUCCESS}: Cleared {count} word(s) from the {lang_code} vocabulary list."


@mcp.tool()
def get_word_examples(word: str, lang_code: str) -> str:
    """
    Retrieve attested example sentences for a word from the dictionary.
    Use this to ground your own example sentence generation in real usage.
    Example inputs:
        get_word_examples("comer", "es")
        get_word_examples("courir", "fr")
    """
    entries = dictionary.describe(word, lang_code)
    lines = []
    for entry in entries:
        for sense in entry.get("senses", []):
            example = sense.get("example", "")
            if example:
                lines.append(f"- {example}")
                translation = sense.get("example_translation", "")
                if translation:
                    lines.append(f"  ({translation})")
    if not lines:
        return f"No attested examples found for '{word}' ({lang_code})."
    return "\n".join(lines)


_GENDER_TAGS = {"masculine", "feminine", "neuter", "common", "common-gender"}


@mcp.tool()
def get_random_vocab_word(lang_code: str) -> str:
    """
    Return a random word from the user's vocabulary list for a given language.
    Use this to start a gender quiz: present the word to the user and ask them
    to guess its grammatical gender, then call check_grammatical_gender to verify.
    If the user does not specify a language, ask them which language before calling this tool.
    Example inputs:
        get_random_vocab_word("es")
        get_random_vocab_word("fr")
    """
    words = vocab_store.list_words(lang_code)
    if not words:
        return f"No vocabulary words saved for '{lang_code}'. Add some words first."
    return random.choice(words)


@mcp.tool()
def check_grammatical_gender(word: str, lang_code: str) -> str:
    """
    Look up the grammatical gender(s) of a word from the dictionary.
    Call this after the user has guessed, to verify their answer.
    Returns the correct gender(s) or a message if gender info is unavailable.
    Example inputs:
        check_grammatical_gender("manzana", "es")
        check_grammatical_gender("chat", "fr")
    """
    entries = dictionary.describe(word, lang_code)
    genders: set[str] = set()
    for entry in entries:
        for sense in entry.get("senses", []):
            for tag in sense.get("tags", []):
                if tag in _GENDER_TAGS:
                    genders.add(tag)
    if not genders:
        return f"No grammatical gender information found for '{word}' ({lang_code})."
    return " or ".join(sorted(genders))


if __name__ == "__main__":
    mcp.run()

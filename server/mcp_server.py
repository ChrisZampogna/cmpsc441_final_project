from fastmcp import FastMCP

from server.local_dictionary import LocalDictionary
from server.remote_dictionary import RemoteDictionary
from server.dictionary_provider import DictionaryProvider
from server.rag_provider import RagProvider
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

_rag: RagProvider | None = None

def get_rag() -> RagProvider:
    global _rag
    if _rag is None:
        _rag = RagProvider(config)
    return _rag

@mcp.tool()
def hello_world() -> str:
    """
    Returns hello world (tests if tool calling is working)
    """
    return "hello world"

@mcp.tool()
def add(a: int, b: int) -> int:
    """
    Add two integers (tests if tool calling is working)
    """
    return a + b

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
    result = dictionary.lookup(word, lower(lang_code))
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

if __name__ == "__main__":
    mcp.run()

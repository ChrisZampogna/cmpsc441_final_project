from fastmcp import FastMCP
from server.local_dictionary import LocalDictionary
from server.remote_dictionary import RemoteDictionary
from server.dictionary_provider import DictionaryProvider
from util.formatting import format_list
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

if __name__ == "__main__":
    mcp.run()

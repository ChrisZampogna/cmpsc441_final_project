# Language Assistant

My CMPSC 441 Final Project - an AI foreign language study assistant

## Features:

- [X] Wiktionary API connectivity
- [X] Get word metadata from API
- [X] Add vocab words to an internal list
- [X] Automatically add collections of vocabulary words based on a category
- [X] Generate example sentences
- [X] Review grammatical gender
- [X] Ask/answer grammar questions (based on RAG)
- [ ] Generate study plans
- [ ] Generate Anki cards

## Prerequisites

- Python 3.13
- [uv](https://docs.astral.sh/uv/)
- [Ollama](https://ollama.com/) with the `qwen3.5:0.8b` model pulled

Pull the model if you haven't already:

```bash
ollama pull qwen3.5:0.8b
```

## Installation

```bash
uv sync
```

## Running

```bash
uv run python main.py
```

Type `/exit` to quit the chat.

## Configuration

Edit `config.jsonc` to adjust behavior:

```jsonc
{
  // "remote" uses the Wiktionary API (recommended — no setup required)
  // "local"  uses a local SQLite database built from a Wiktionary dump
  "dictionaryProvider": "remote",

  // Any Ollama model that supports tool calling
  // qwen3.5:0.8b is recommended for speed
  "model": "qwen3.5:0.8b"
}
```

The defaults are chosen for the best out-of-the-box experience - the remote dictionary works immediately and the 0.8B model responds quickly. Larger models and the local database are available but require additional setup (see below).

## Optional: local dictionary setup

The local dictionary provider queries a SQLite database built from a full Wiktionary data dump (~2 GB download, ~20GB on disk after processing). Only do this if you have the space and want fully offline operation.

```bash
uv run python setup.py
```

This downloads, extracts, and indexes the data into `data/generated/wiktionary.db`. Once complete, set `"dictionaryProvider": "local"` in `config.jsonc`.

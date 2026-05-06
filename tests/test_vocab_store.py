import unicodedata

import pytest

from server.vocab_store import VocabStore


@pytest.fixture
def store(tmp_path):
    return VocabStore(tmp_path / "vocab.db")


def test_add_word_success(store):
    assert store.add_word("hola", "es") is True
    assert store.list_words("es") == ["hola"]


def test_add_word_duplicate(store):
    store.add_word("hola", "es")
    assert store.add_word("hola", "es") is False
    assert store.list_words("es") == ["hola"]


def test_add_words_bulk(store):
    added, skipped = store.add_words(["manzana", "pollo", "arroz"], "es")
    assert added == 3
    assert skipped == 0


def test_add_words_bulk_with_duplicates(store):
    store.add_word("manzana", "es")
    added, skipped = store.add_words(["manzana", "pollo"], "es")
    assert added == 1
    assert skipped == 1


def test_remove_word(store):
    store.add_word("hola", "es")
    assert store.remove_word("hola", "es") is True
    assert store.list_words("es") == []


def test_remove_word_not_found(store):
    assert store.remove_word("hola", "es") is False


def test_list_words_sorted(store):
    store.add_words(["pollo", "arroz", "manzana"], "es")
    assert store.list_words("es") == ["arroz", "manzana", "pollo"]


def test_list_words_empty(store):
    assert store.list_words("es") == []


def test_list_words_per_language(store):
    store.add_word("hola", "es")
    store.add_word("bonjour", "fr")
    assert store.list_words("es") == ["hola"]
    assert store.list_words("fr") == ["bonjour"]


def test_clear_words(store):
    store.add_words(["hola", "adios"], "es")
    count = store.clear_words("es")
    assert count == 2
    assert store.list_words("es") == []


def test_clear_words_does_not_affect_other_language(store):
    store.add_word("hola", "es")
    store.add_word("bonjour", "fr")
    store.clear_words("es")
    assert store.list_words("fr") == ["bonjour"]


def test_word_exists_true(store):
    store.add_word("hola", "es")
    assert store.word_exists("hola", "es") is True


def test_word_exists_false(store):
    assert store.word_exists("hola", "es") is False


def test_unicode_normalization(store):
    nfc = unicodedata.normalize("NFC", "café")
    nfd = unicodedata.normalize("NFD", "café")
    store.add_word(nfc, "fr")
    # NFD-encoded query should find the NFC-stored word
    assert store.word_exists(nfd, "fr") is True
    assert store.remove_word(nfd, "fr") is True
    assert store.list_words("fr") == []

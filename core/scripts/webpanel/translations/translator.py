"""
This module handles translations for the webpanel.

It loads all JSON files in the same directory as this file and stores
them in a dictionary where the key is the language code and the value
is another dictionary with the translations.

The `translator` function returns the translated text for the given
language code. If the language code is not found, it returns the
original text.

The `get_langs` function returns a list of all language codes.
"""

from pathlib import Path
import json


TRANSLATIONS = {}

for lang_file in Path(__file__).parent.iterdir():
    if lang_file.suffix == ".json":
        with open(lang_file, "r", encoding="utf-8") as f:
            TRANSLATIONS[lang_file.stem] = json.load(f)


def translator(key: str, lang: str) -> str:
    """
    Returns the translated text for the given language code.

    Args:
        key (str): The key to translate.
        lang (str): The language code.

    Returns:
        str: The translated key.
    """
    if lang not in get_langs():
        return key
    return TRANSLATIONS[lang].get(key, key)


def get_langs() -> list[str]:
    """
    Returns a list of all language codes.

    Returns:
        List[str]: A list of language codes.
    """
    return list(TRANSLATIONS.keys())

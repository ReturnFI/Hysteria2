from pathlib import Path
import json


TRANSLATIONS = {}

for lang_file in Path(__file__).parent.iterdir():
    if lang_file.suffix == ".json":
        with open(lang_file, "r", encoding="utf-8") as f:
            TRANSLATIONS[lang_file.stem] = json.load(f)


def translator(text: str, lang) -> str:
    if lang not in get_langs():
        return text
    return TRANSLATIONS[lang].get(text, text)


def get_langs():
    return list(TRANSLATIONS.keys())

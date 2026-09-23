"""Every text exists in both languages, and every key the program uses exists."""
import os
import re

from lythossettle.i18n import ENTRIES, TRANSLATIONS
from lythossettle.web.strings import REUSED, SHELL, shell_strings

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lythossettle")


def test_both_languages_are_complete():
    assert set(TRANSLATIONS["en"]) == set(TRANSLATIONS["tr"])
    for key, (en, tr) in ENTRIES.items():
        assert en and tr, key
        # the same placeholders in both, or a format() call would fail in one language
        assert set(re.findall(r"{(\w+)", en)) == set(re.findall(r"{(\w+)", tr)), key


def test_the_shell_strings_exist_in_both_languages():
    english, turkish = shell_strings("en"), shell_strings("tr")
    assert set(english) == set(turkish) == set(SHELL) | set(REUSED)
    assert all(english[key] for key in english)


def test_every_literal_key_the_program_reads_is_translated():
    """L["key"] and self.t["key"] in the source must name an entry."""
    used = set()
    for folder, _, files in os.walk(ROOT):
        for name in files:
            if name.endswith(".py"):
                source = open(os.path.join(folder, name), encoding="utf-8").read()
                used |= set(re.findall(r'\b(?:L|self\.L|self\.t)\["([a-z0-9_]+)"\]', source))
    missing = sorted(key for key in used if key not in TRANSLATIONS["en"])
    assert not missing, missing

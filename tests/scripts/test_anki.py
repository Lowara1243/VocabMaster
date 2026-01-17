import pytest
import re
from scripts.csv_to_anki import format_text

def test_format_text():
    assert format_text("Hello #world#") == "Hello <b>world</b>"
    assert format_text("No hashtags") == "No hashtags"
    assert format_text("#multiple# #tags#") == "<b>multiple</b> <b>tags</b>"
    assert format_text("") == ""
    assert format_text(None) == ""

import sys
import os

# Add backend to path to import main
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from main import split_text_respecting_brackets


def test_splitting():
    test_cases = [
        ("word1, word2", ["word1", "word2"]),
        ("word1, [ctx, 2], word3", ["word1", "[ctx, 2]", "word3"]),
        ("[nested, [inner, bracket]], outer", ["[nested, [inner, bracket]]", "outer"]),
        ("", []),
        ("   ", []),
        ("word1,", ["word1"]),
    ]

    for input_txt, expected in test_cases:
        result = split_text_respecting_brackets(input_txt)
        assert result == expected, (
            f"Failed for '{input_txt}': expected {expected}, got {result}"
        )
        print(f"PASS: '{input_txt}' -> {result}")


if __name__ == "__main__":
    try:
        test_splitting()
        print("All backend splitting tests passed!")
    except ImportError:
        print(
            "Could not import backend.main. Ensure you are running this from the project root."
        )
    except Exception as e:
        print(f"Test failed: {e}")
        sys.exit(1)

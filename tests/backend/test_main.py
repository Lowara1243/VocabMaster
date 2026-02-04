import pytest
from backend.main import (
    clean_csv_field,
    parse_word_with_context,
    get_prompt_template,
    app,
    extract_data_line,
    format_error_response,
)
from fastapi.testclient import TestClient

client = TestClient(app)


def test_clean_csv_field():
    assert clean_csv_field("hello") == "hello"
    assert clean_csv_field("hello\nworld") == "hello world"
    assert clean_csv_field('He said "Hi"') == 'He said ""Hi""'
    assert clean_csv_field("  spaces  ") == "spaces"
    assert (
        clean_csv_field("multiple\n\nnewlines") == "multiple newlines"
    )  # re.sub(r'\s+', ' ', ...)


def test_parse_word_with_context():
    # Rule 1: Text outside brackets
    assert parse_word_with_context("[context] word") == ("word", "context")
    assert parse_word_with_context("word [context]") == ("word", "context")
    assert parse_word_with_context("[ctx1] word [ctx2]") == ("word", "ctx1 ... ctx2")

    # Rule 2: Entire string bracketed
    assert parse_word_with_context("[word]") == ("word", None)
    assert parse_word_with_context("[word][context]") == ("word", "context")

    # No brackets
    assert parse_word_with_context("plain word") == ("plain word", None)


def test_get_prompt_template_fallback(tmp_path, monkeypatch):
    # Mock PROMPTS_DIR
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    (prompts_dir / "prompt.txt").write_text("default")
    (prompts_dir / "prompt_German.txt").write_text("german_source")
    (prompts_dir / "prompt_German_Russian.txt").write_text("german_russian_pair")

    monkeypatch.setattr("backend.main.PROMPTS_DIR", str(prompts_dir))
    monkeypatch.setattr("backend.main.DEFAULT_PROMPT_TEMPLATE", "default")

    # 1. Full pair match
    assert get_prompt_template("German", "Russian") == "german_russian_pair"

    # 2. Source only match
    assert get_prompt_template("German", "English") == "german_source"

    # 3. Default fallback
    assert get_prompt_template("French", "Russian") == "default"


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_process_words_invalid_request():
    response = client.post(
        "/process-words", json={"text": "", "source_lang": "En", "target_lang": "Ru"}
    )
    assert response.status_code == 422  # Pydantic validation error for min_length=1


def test_extract_data_line_no_examples():
    """Test extract_data_line with zero examples."""
    stdout = """
    ```json
    {
        "infinitive": "was ist das?",
        "transcription": "[vas ɪst das]",
        "translations": ["what is that?"],
        "examples": []
    }
    ```
    """
    raw_word = "was ist das?"
    parsed_word = "was ist das?"
    expected_csv = '"was ist das?";"[vas ɪst das]";"what is that?";"was ist das?"'  # infinitive;transcription;translations;id_raw
    assert extract_data_line(stdout, raw_word, parsed_word) == expected_csv


def test_extract_data_line_one_example():
    """Test extract_data_line with one example."""
    stdout = """
    ```json
    {
        "infinitive": "run",
        "transcription": "[rʌn]",
        "translations": ["бежать"],
        "examples": [
            {"source": "I #run#.", "translation": "Я #бегаю#."}
        ]
    }
    ```
    """
    raw_word = "run"
    parsed_word = "run"
    expected_csv = '"run";"[rʌn]";"бежать";"I #run#.";"Я #бегаю#.";"run"'  # infinitive;transcription;translations;source1;translation1;id_raw
    assert extract_data_line(stdout, raw_word, parsed_word) == expected_csv


def test_extract_data_line_two_examples():
    """Test extract_data_line with two examples."""
    stdout = """
    ```json
    {
        "infinitive": "obnoxious",
        "transcription": "[əbˈnɒkʃəs]",
        "translations": ["неприятный"],
        "examples": [
            {"source": "He is #obnoxious#.", "translation": "Он #неприятный#."},
            {"source": "That was #obnoxious#.", "translation": "Это было #отвратительно#."}
        ]
    }
    ```
    """
    raw_word = "obnoxious"
    parsed_word = "obnoxious"
    expected_csv = '"obnoxious";"[əbˈnɒkʃəs]";"неприятный";"He is #obnoxious#.";"Он #неприятный#.";"That was #obnoxious#.";"Это было #отвратительно#.";"obnoxious"'  # infinitive;transcription;translations;source1;translation1;source2;translation2;id_raw
    assert extract_data_line(stdout, raw_word, parsed_word) == expected_csv


def test_extract_data_line_typo_correction():
    """Test extract_data_line with typo correction in infinitive."""
    stdout = """
    ```json
    {
        "infinitive": "obnoxious",
        "transcription": "[əbˈnɒkʃəs]",
        "translations": ["неприятный"],
        "examples": []
    }
    ```
    """
    raw_word = "obnoxius"
    parsed_word = "obnoxius"
    expected_csv = '"obnoxious";"[əbˈnɒkʃəs]";"неприятный";"obnoxius"'  # infinitive;transcription;translations;id_raw
    assert extract_data_line(stdout, raw_word, parsed_word) == expected_csv


def test_extract_data_line_malformed_json():
    """Test extract_data_line with malformed JSON output from model."""
    stdout = "This is not JSON at all."
    raw_word = "test"
    parsed_word = "test"
    with pytest.raises(ValueError, match="No JSON object found in output"):
        extract_data_line(stdout, raw_word, parsed_word)


def test_format_error_response():
    """Test format_error_response."""
    raw_word = "invalid"
    error_message = "Some error occurred"
    # Format: Display;"[error]";"[ERROR]: ...";ID
    expected_csv = '"invalid";"[error]";"[ERROR]: Some error occurred";"invalid"'
    assert format_error_response(raw_word, error_message) == expected_csv

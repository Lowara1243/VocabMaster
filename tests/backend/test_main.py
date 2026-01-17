import pytest
from backend.main import clean_csv_field, parse_word_with_context, get_prompt_template, app
from fastapi.testclient import TestClient
import re

client = TestClient(app)

def test_clean_csv_field():
    assert clean_csv_field("hello") == "hello"
    assert clean_csv_field("hello\nworld") == "hello world"
    assert clean_csv_field('He said "Hi"') == 'He said ""Hi""'
    assert clean_csv_field("  spaces  ") == "spaces"
    assert clean_csv_field("multiple\n\nnewlines") == "multiple newlines" # re.sub(r'\s+', ' ', ...)

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
    response = client.post("/process-words", json={"text": "", "source_lang": "En", "target_lang": "Ru"})
    assert response.status_code == 422 # Pydantic validation error for min_length=1

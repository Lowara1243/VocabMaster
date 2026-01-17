"""Word processing API using Gemini CLI."""

import os
import subprocess
import asyncio
import json
import logging
import re
from typing import AsyncGenerator

from fastapi.concurrency import run_in_threadpool
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Configuration
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
MAX_WORDS_PER_REQUEST = 50
COMMAND_TIMEOUT = 120
LOG_LEVEL_STR = os.getenv("LOG_LEVEL", "INFO").upper()

try:
    MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "5"))
except ValueError:
    MAX_CONCURRENT_REQUESTS = 5

# Set up logging
LOG_LEVEL = getattr(logging, LOG_LEVEL_STR, logging.INFO)
# Use logs directory in the project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'backend.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class WordsRequest(BaseModel):
    """Request model for word processing."""
    text: str = Field(..., min_length=1, max_length=5000)
    source_lang: str = Field("English", description="Source language name")
    target_lang: str = Field("Russian", description="Target language name")


app = FastAPI(
    title="Word Processor API",
    description="API for processing words with Gemini",
    version="0.1.0",
)

# Simple CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PROMPTS_DIR = ""

try:
    # Use paths relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    PROMPTS_DIR = os.path.join(script_dir, 'prompts')
    with open(os.path.join(PROMPTS_DIR, 'prompt.txt'), 'r') as f:
        DEFAULT_PROMPT_TEMPLATE = f.read().strip()
    with open(os.path.join(PROMPTS_DIR, 'fix_json_prompt.txt'), 'r') as f:
        FIX_JSON_PROMPT_TEMPLATE = f.read().strip()
except FileNotFoundError as e:
    raise SystemExit(f"Error: Prompt file not found - {e.filename}. Please check the backend/prompts/ directory.")


def get_prompt_template(source_lang: str, target_lang: str) -> str:
    """
    Get the appropriate prompt template.
    Tries to find a specific prompt for the language pair (e.g., prompt_German_Russian.txt).
    Falls back to the default prompt.txt.
    """
    # Sanitize language names to prevent directory traversal or invalid filenames
    safe_source = "".join([c for c in source_lang if c.isalnum()])
    safe_target = "".join([c for c in target_lang if c.isalnum()])
    
    specific_prompt_filename = f"prompt_{safe_source}_{safe_target}.txt"
    specific_prompt_path = os.path.join(PROMPTS_DIR, specific_prompt_filename)
    
    if os.path.exists(specific_prompt_path):
        try:
            with open(specific_prompt_path, 'r') as f:
                logger.debug(f"Using specific prompt: {specific_prompt_filename}")
                return f.read().strip()
        except Exception as e:
            logger.warning(f"Failed to read specific prompt {specific_prompt_filename}: {e}. Using default.")
            
    # Fallback to source-only prompt
    source_only_filename = f"prompt_{safe_source}.txt"
    source_only_path = os.path.join(PROMPTS_DIR, source_only_filename)
    if os.path.exists(source_only_path):
        try:
            with open(source_only_path, 'r') as f:
                logger.debug(f"Using source-specific prompt: {source_only_filename}")
                return f.read().strip()
        except Exception as e:
            logger.warning(f"Failed to read source-specific prompt {source_only_filename}: {e}. Using default.")

    return DEFAULT_PROMPT_TEMPLATE


def build_prompt(word: str, source_lang: str, target_lang: str, context: str | None = None) -> str:
    """Build prompt for Gemini CLI."""
    
    template = get_prompt_template(source_lang, target_lang)

    context_prompt = ""
    if context:
        context_prompt = f"Given the context `{context}`, "

    return template.format(
        word=word,
        source_lang=source_lang,
        target_lang=target_lang,
        context_prompt=context_prompt
    ).replace("\n", " ").strip()


def clean_csv_field(text: str) -> str:
    """Clean text for CSV field: remove all whitespace/newlines and escape double quotes."""
    if not isinstance(text, str):
        text = str(text)
    # Replace literal \n and \r if they exist as strings
    text = text.replace("\\n", " ").replace("\\r", " ")
    # Replace any sequence of whitespace with a single space
    return re.sub(r'\s+', ' ', text).replace('"', '""').strip()


def extract_data_line(stdout: str, raw_word: str, parsed_word: str) -> str:
    """Extract data from Gemini output, convert to CSV."""
    try:
        # Regex to find JSON block, including markdown ```json ... ```
        match = re.search(r'```json\s*(\{.*?\})\s*```|(\{.*?\})', stdout, re.DOTALL)
        if not match:
            raise ValueError("No JSON object found in output")

        # Get the first non-empty group
        json_str = next((g for g in match.groups() if g), None)
        if not json_str:
            raise ValueError("No JSON content extracted")

        data = json.loads(json_str)


        # Extract fields with defaults and clean them
        infinitive = clean_csv_field(data.get("infinitive", parsed_word))
        transcription = clean_csv_field(data.get("transcription", ""))
        translations = clean_csv_field(", ".join(data.get("translations", [])))

        examples = data.get("examples", [])
        example_fields = []
        for ex in examples:
            source = clean_csv_field(ex.get("source", ""))
            translation = clean_csv_field(ex.get("translation", ""))
            example_fields.append(f'"{source}"')
            example_fields.append(f'"{translation}"')
        
        # Ensure at least two pairs of examples (even if empty) for basic compatibility
        while len(example_fields) < 4:
            example_fields.append('""')
            
        examples_str = ";".join(example_fields)

        # Format as CSV line for ReWord:
        # 1. infinitive, 2. transcription, 3. translations, 4. examples...
        return (
            f'"{infinitive}";"{transcription}";"{translations}";{examples_str}'
        )

    except (json.JSONDecodeError, ValueError, KeyError, IndexError) as e:
        # Error is logged in the calling function with more context
        raise ValueError(f"Invalid response format: {e}")


def format_error_response(raw_word: str, error_message: str) -> str:
    """Format error as CSV line."""
    error_message = error_message.replace('"', '""')
    # Use raw_word as the first field
    return f'"{raw_word}";"{error_message}";"[error]";"";""'


async def fix_json_with_llm(broken_output: str, original_word: str) -> str | None:
    """Attempt to fix a broken JSON string using an LLM."""
    if not broken_output or not broken_output.strip():
        return None

    logger.info(f"Attempting to fix JSON for word '{original_word}'")
    prompt = FIX_JSON_PROMPT_TEMPLATE.format(broken_output=broken_output)
    command = ["gemini", "-m", GEMINI_MODEL, "-p", prompt]

    try:
        result = await run_in_threadpool(
            subprocess.run,
            command,
            capture_output=True,
            text=True,
            check=True,
            timeout=COMMAND_TIMEOUT,
            stdin=subprocess.DEVNULL,
        )
        fixed_output = result.stdout

        # We need to re-extract the JSON from the model's response
        match = re.search(r'```json\s*(\{.*?\})\s*```|(\{.*?\})', fixed_output, re.DOTALL)
        if not match:
            logger.warning(f"JSON-fixing LLM did not return a JSON object for '{original_word}'.")
            return None

        json_str = next((g for g in match.groups() if g), None)
        if not json_str:
            logger.warning(f"JSON-fixing LLM returned empty JSON content for '{original_word}'.")
            return None

        # Verify if the fixed string is valid JSON before returning
        json.loads(json_str)
        # Return the full output, which contains the verified JSON.
        return fixed_output

    except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
        logger.error(f"Error while trying to fix JSON for '{original_word}': {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse the 'fixed' JSON for '{original_word}': {e}. Output was:\n{fixed_output}")
        return None
    except Exception as e:
        logger.exception(f"An unexpected error occurred while fixing JSON for '{original_word}'")
        return None


async def get_word_details(raw_word: str, parsed_word: str, source_lang: str, target_lang: str, context: str | None = None) -> str:
    """Fetch word details from Gemini CLI with retries. Returns CSV-formatted string."""
    prompt = build_prompt(parsed_word, source_lang, target_lang, context)
    command = ["gemini", "-m", GEMINI_MODEL, "-p", prompt]
    max_retries = 3

    last_error = "Unknown error"
    last_stdout = None

    for attempt in range(max_retries):
        try:
            logger.info(f"Processing word: '{raw_word}' (Attempt {attempt + 1}/{max_retries})")

            result = await run_in_threadpool(
                subprocess.run,
                command,
                capture_output=True,
                text=True,
                check=True,
                timeout=COMMAND_TIMEOUT,
                stdin=subprocess.DEVNULL,
            )
            last_stdout = result.stdout

            if not last_stdout.strip():
                raise ValueError("Empty response from model")

            # If we are here, we got a non-empty response, try to parse it
            return extract_data_line(last_stdout, raw_word, parsed_word)

        except ValueError as e:
            # This catches both parsing errors from extract_data_line and the empty response error
            logger.warning(f"Attempt {attempt + 1} failed for '{raw_word}': {e}")
            
            # If it is a JSON error, try to fix it
            if ("JSON" in str(e) or "delimiter" in str(e)) and last_stdout:
                fixed_json_str = await fix_json_with_llm(last_stdout, raw_word)
                if fixed_json_str:
                    try:
                        # If fixing succeeds, pass the fixed string to the data extractor.
                        # The extractor can handle a raw JSON string.
                        logger.info(f"Successfully fixed JSON for '{raw_word}'.")
                        return extract_data_line(fixed_json_str, raw_word, parsed_word)
                    except ValueError as fix_e:
                        logger.warning(f"Failed to process the 'fixed' JSON for '{raw_word}': {fix_e}")
                        last_error = f"Malformed data that could not be fixed: {fix_e}"
                else:
                    last_error = "Malformed data that could not be fixed."
            else:
                 last_error = f"Invalid response from model: {e}"

            if attempt < max_retries - 1:
                await asyncio.sleep(1)  # Wait 1 second before next attempt
            continue # Go to next attempt

        except FileNotFoundError:
            logger.error("gemini-cli not found in PATH")
            last_error = "Server configuration error: gemini-cli not found"
            break  # No point retrying if the command doesn't exist

        except subprocess.TimeoutExpired:
            logger.error(f"Timeout processing '{raw_word}' after {COMMAND_TIMEOUT}s")
            last_error = f"Timeout: processing took longer than {COMMAND_TIMEOUT} seconds."
            # Don't break, allow for retry if the timeout was a fluke
            if attempt >= max_retries - 1:
                 break


        except subprocess.CalledProcessError as e:
            last_stdout = e.stdout
            logger.error(f"Command failed for '{raw_word}': {e.stderr}")
            stderr_lower = e.stderr.lower() if e.stderr else ""
            if "auth" in stderr_lower:
                last_error = "Server authorization error with Gemini API"
            elif any(kw in stderr_lower for kw in ["connection", "network"]):
                last_error = "Network error when connecting to Gemini API"
            elif "capacity" in stderr_lower:
                last_error = "API capacity exhausted. Please try again later."
            else:
                last_error = "Error executing gemini-cli command"
            
            if attempt >= max_retries - 1:
                break


        except Exception as e:
            logger.exception(f"An unexpected error occurred while processing '{raw_word}'")
            last_error = f"An unexpected server error occurred: {str(e)}"
            break # Unexpected error, break immediately

    # All retries failed
    log_message = f"All {max_retries} attempts failed for '{raw_word}'. Last error: {last_error}"
    if last_stdout:
        log_message += f"\nLast raw output:\n---\n{last_stdout}\n---"
    
    logger.error(log_message)
    return format_error_response(raw_word, last_error)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


def parse_word_with_context(text: str) -> tuple[str, str | None]:
    """
    Parses a string to extract a word and optional context.

    Rule 1: If there is text outside of brackets, that text is the "word"
            and the text inside brackets is the "context".
            e.g. "[he brought it] upon [himself]" -> word: "upon", context: "he brought it ... himself"

    Rule 2: If the entire string is bracketed, the content of the first
            bracket is the "word" and subsequent brackets are "context".
            e.g. "[upon himself]" -> word: "upon himself", context: None
            e.g. "[he brought it][upon himself]" -> word: "he brought it", context: "upon himself"
    """
    bracket_content = re.findall(r"\[(.*?)\]", text)
    
    # Using re.sub to get text outside brackets.
    text_with_placeholders = re.sub(r'\[.*?\]', ' ', text)

    # If after stripping whitespace, there is something left, then Rule 1 applies.
    if text_with_placeholders.strip():
        # Rule 1
        word = text_with_placeholders.strip()
        context = " ... ".join(bracket_content) if bracket_content else None
        return word, context
    else:
        # Rule 2
        if not bracket_content:
            # No brackets, no text outside, it's an empty or whitespace string
            return text.strip(), None
        
        # The word is the content of the first bracket
        word = bracket_content[0]
        
        # Context is made of subsequent brackets
        if len(bracket_content) > 1:
            context = " ... ".join(bracket_content[1:])
        else:
            context = None
        return word.strip(), context


@app.post("/process-words")
async def process_words(request: WordsRequest) -> StreamingResponse:
    """Process comma-separated words and stream results as CSV lines."""
    
    raw_words = [w.strip() for w in request.text.split(",") if w.strip()]
    
    if not raw_words:
        raise HTTPException(status_code=400, detail="No valid words provided")

    if len(raw_words) > MAX_WORDS_PER_REQUEST:
        raise HTTPException(
            status_code=400,
            detail=f"Too many words. Maximum: {MAX_WORDS_PER_REQUEST}",
        )

    # Create a list of requests to process, without de-duplication
    requests_to_process = []
    for raw_word in raw_words:
        parsed_word, context = parse_word_with_context(raw_word)
        if parsed_word:
            requests_to_process.append((raw_word, parsed_word.lower(), context))

    logger.info(f"Processing {len(requests_to_process)} words from {request.source_lang} to {request.target_lang}")

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    async def constrained_get_word_details(raw_word: str, parsed_word: str, source_lang: str, target_lang: str, context: str | None = None) -> str:
        async with semaphore:
            try:
                return await get_word_details(raw_word, parsed_word, source_lang, target_lang, context)
            except Exception as e:
                logger.exception(f"Error processing '{raw_word}'")
                return format_error_response(raw_word, f"Error: {str(e)}")

    async def stream_results() -> AsyncGenerator[str, None]:
        """Generate CSV lines for each processed word as they complete."""
        tasks = [
            constrained_get_word_details(raw_word, parsed_word, request.source_lang, request.target_lang, context)
            for raw_word, parsed_word, context in requests_to_process
        ]
        
        for task in asyncio.as_completed(tasks):
            result = await task
            yield f"{result}\n"

    return StreamingResponse(
        stream_results(),
        media_type="text/plain; charset=utf-8",
        headers={
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "no-cache",
        },
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

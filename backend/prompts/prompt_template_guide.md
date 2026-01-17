# Prompt Templates Guide

The VocabMaster backend supports language-specific prompt templates. This allows you to customize the instructions sent to the Gemini model based on the selected source and target languages.

## File Naming Convention

To create a specific prompt for a language pair, create a new text file in the `backend/prompts/` directory with the following name format:

- `prompt_{SourceLanguage}_{TargetLanguage}.txt`: Specific to both source and target.
- `prompt_{SourceLanguage}.txt`: Specific only to the source language (handles rules like "to" for English verbs or articles for German nouns).

- `SourceLanguage`: The name of the source language (e.g., English, German).
- `TargetLanguage`: The name of the target language (e.g., Russian).

**Note:** The language names must match exactly what is sent from the frontend (case-sensitive, but the system cleans them to be alphanumeric only).

### Examples

- `prompt_English_Russian.txt`: Used when translating from English to Russian.
- `prompt_English.txt`: Used for any English source translation if a pair-specific prompt isn't found.
- `prompt_German.txt`: Used for any German source translation (handles articles).

## Fallback Mechanism

1.  Look for `prompt_{Source}_{Target}.txt`.
2.  If not found, look for `prompt_{Source}.txt`.
3.  If still not found, default to `prompt.txt`.

## Template Variables

Your prompt template can use the following placeholders, which will be replaced by the actual values at runtime:

- `{word}`: The word or phrase to process.
- `{source_lang}`: The source language name.
- `{target_lang}`: The target language name.
- `{context_prompt}`: This will be populated with "Given the context `[context]`, " if context is provided, or an empty string otherwise.

## Example Template

```text
{context_prompt}For the word/phrase "{word}", which is in {source_lang}, provide ONLY a JSON object:
- "infinitive": The base form...
...
```

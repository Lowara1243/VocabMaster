import csv
import genanki
import sys
import argparse
import re

# --- Configuration ---
MODEL_ID = 1607392319
DECK_ID = 2059400110

# CSS for the card - Elegant and readable
CSS = """
.card {
  font-family: 'Segoe UI', Arial, sans-serif;
  font-size: 20px;
  text-align: center;
  color: #333;
  background-color: #fcfcfc;
  padding: 20px;
}
.word {
  font-size: 48px;
  font-weight: bold;
  color: #0056b3;
  margin-bottom: 2px;
}
.transcription {
  font-size: 22px;
  color: #666;
  font-family: 'Arial', sans-serif;
  margin-bottom: 20px;
}
.translation-box {
  background: #e7f3ff;
  border-radius: 8px;
  padding: 15px;
  margin: 15px 0;
  border: 1px solid #cce5ff;
}
.translation {
  font-size: 30px;
  font-weight: bold;
  color: #004085;
}
.examples-container {
  text-align: left;
  margin-top: 30px;
  padding: 20px;
  background-color: #fff;
  border: 1px solid #ddd;
  border-radius: 10px;
  box-shadow: 0 2px 5px rgba(0,0,0,0.05);
}
.example-item {
  margin-bottom: 15px;
}
.example-en {
  font-size: 21px;
  margin-bottom: 5px;
  color: #222;
  line-height: 1.4;
}
.example-ru {
  color: #555;
  font-style: italic;
  font-size: 19px;
}
.example-divider {
  border: 0;
  border-top: 1px dashed #ccc;
  margin: 15px 0;
}
b, strong {
  color: #d9534f;
  background-color: #fff9f9;
  padding: 0 2px;
  border-radius: 3px;
}
"""

# HTML templates
# Question: Show the word (Original input)
Q_FMT = '<div class="word">{{Word}}</div>'

# Answer: Show transcription, translations and ALL examples
# We use a single field for all examples since Anki fields are fixed at Model level
A_FMT = """
<div class="word">{{Infinitive}}</div>
{{#Transcription}}
<div class="transcription">{{Transcription}}</div>
{{/Transcription}}

<hr id="answer">

<div class="translation-box">
    <div class="translation">{{Translations}}</div>
</div>

{{#Examples_HTML}}
<div class="examples-container">
    {{Examples_HTML}}
</div>
{{/Examples_HTML}}
"""

# Reverse Card HTML templates
# Question: Show translations (Native language)
Q_FMT_REVERSE = """
<div class="translation-box">
    <div class="translation">{{Translations}}</div>
</div>
"""

# Answer: Show translations, then word, transcription, and examples
A_FMT_REVERSE = """
<div class="translation-box">
    <div class="translation">{{Translations}}</div>
</div>

<hr id="answer">

<div class="word">{{Infinitive}}</div>
{{#Transcription}}
<div class="transcription">{{Transcription}}</div>
{{/Transcription}}

{{#Examples_HTML}}
<div class="examples-container">
    {{Examples_HTML}}
</div>
{{/Examples_HTML}}
"""


def create_model():
    return genanki.Model(
        MODEL_ID,
        "VocabMaster V3 (Dynamic)",
        fields=[
            {"name": "Word"},  # 0: original input (Foreign word)
            {"name": "Infinitive"},  # 1: base form (Foreign word)
            {"name": "Transcription"},  # 2: IPA
            {"name": "Translations"},  # 3: target lang (Native translations)
            {"name": "Examples_HTML"},  # 4: All examples rendered as HTML
        ],
        css=CSS,
    )


def format_text(text):
    """Converts #word# to <b>word</b> for Anki's HTML display."""
    if not text:
        return ""
    return re.sub(r"#([^#]+)#", r"<b>\1</b>", text)


def csv_to_apkg(input_file, output_file, deck_name, card_type_arg):
    # 1. Determine card_type
    card_type = card_type_arg
    if card_type_arg == "foreign-native":
        print("\nSelect card generation type:")
        print("1. Foreign to Native (e.g., English word -> Russian translation)")
        print("2. Native to Foreign (e.g., Russian translation -> English word)")
        print("3. Bidirectional (both 1 and 2)")

        while True:
            choice = input("Enter your choice (1, 2, or 3): ").strip()
            if choice == "1":
                card_type = "foreign-native"
                break
            elif choice == "2":
                card_type = "native-foreign"
                break
            elif choice == "3":
                card_type = "bidirectional"
                break
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")

    # 2. Build templates based on card_type
    templates_to_use = []
    if card_type == "foreign-native" or card_type == "bidirectional":
        templates_to_use.append(
            {
                "name": "Vocabulary Card (Foreign to Native)",
                "qfmt": Q_FMT,
                "afmt": A_FMT,
            }
        )
    if card_type == "native-foreign" or card_type == "bidirectional":
        templates_to_use.append(
            {
                "name": "Vocabulary Card (Native to Foreign)",
                "qfmt": Q_FMT_REVERSE,
                "afmt": A_FMT_REVERSE,
            }
        )

    # 3. Create Model
    base_model_props = create_model()
    model = genanki.Model(
        base_model_props.model_id,
        base_model_props.name,
        fields=base_model_props.fields,
        templates=templates_to_use,
        css=base_model_props.css,
    )

    # 4. Create Deck
    deck = genanki.Deck(DECK_ID, deck_name)

    # 5. Process CSV and create notes
    count = 0
    try:
        with open(input_file, mode="r", encoding="utf-8-sig") as f:
            reader = csv.reader(f, delimiter=";")
            for row in reader:
                # New Format: word(infinitive);transcription;translations;ex1_en;ex1_ru;...
                if not row or len(row) < 3:
                    continue

                # Build examples HTML
                examples_html = []
                # Examples start from index 3
                for i in range(3, len(row) - 1, 2):
                    source = row[i]
                    translation = row[i + 1] if i + 1 < len(row) else ""

                    if not source and not translation:
                        continue

                    if examples_html:
                        examples_html.append('<div class="example-divider"></div>')

                    examples_html.append('<div class="example-item">')
                    examples_html.append(
                        f'  <div class="example-en">{format_text(source)}</div>'
                    )
                    examples_html.append(
                        f'  <div class="example-ru">{format_text(translation)}</div>'
                    )
                    examples_html.append("</div>")

                fields = [
                    row[0],  # Word (Front)
                    row[0],  # Infinitive (Back - same as word now)
                    row[1],  # Transcription
                    row[2],  # Translations
                    "".join(examples_html),  # Examples_HTML
                ]

                # A single note will generate one or two cards based on the templates in the model
                note = genanki.Note(model=model, fields=fields)
                deck.add_note(note)
                count += 1

        genanki.Package(deck).write_to_file(output_file)

        # Adjust count for bidirectional cards for user feedback
        final_card_count = count
        if card_type == "bidirectional":
            final_card_count *= 2

        print(f"Successfully created {output_file} with {final_card_count} cards.")

    except FileNotFoundError:
        print(f"Error: File {input_file} not found.")
    except Exception as e:
        print(f"An error occurred: {e} - {type(e).__name__}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert VocabMaster CSV to Anki .apkg"
    )
    parser.add_argument("input", help="Path to input CSV file")
    parser.add_argument(
        "-o", "--output", help="Path to output .apkg file", default="vocab_deck.apkg"
    )
    parser.add_argument(
        "-n", "--name", help="Anki deck name", default="VocabMaster Deck"
    )
    parser.add_argument(
        "-t",
        "--card-type",
        choices=["foreign-native", "native-foreign", "bidirectional"],
        default="foreign-native",
        help="Type of cards to generate: 'foreign-native' (default), 'native-foreign', or 'bidirectional'. If not provided, an interactive menu will appear.",
    )

    args = parser.parse_args()
    csv_to_apkg(args.input, args.output, args.name, args.card_type)

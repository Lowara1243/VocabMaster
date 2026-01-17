import csv
import genanki
import sys
import os
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

def create_model():
    return genanki.Model(
        MODEL_ID,
        'VocabMaster V3 (Dynamic)',
        fields=[
            {'name': 'Word'},           # 0: original input
            {'name': 'Infinitive'},     # 1: base form
            {'name': 'Transcription'},  # 2: IPA
            {'name': 'Translations'},   # 3: target lang
            {'name': 'Examples_HTML'},  # 4: All examples rendered as HTML
        ],
        templates=[
            {
                'name': 'Vocabulary Card',
                'qfmt': Q_FMT,
                'afmt': A_FMT,
            },
        ],
        css=CSS
    )

def format_text(text):
    """Converts #word# to <b>word</b> for Anki's HTML display."""
    if not text:
        return ""
    return re.sub(r'#([^#]+)#', r'<b>\1</b>', text)

def csv_to_apkg(input_file, output_file, deck_name):
    model = create_model()
    deck = genanki.Deck(DECK_ID, deck_name)
    
    count = 0
    try:
        with open(input_file, mode='r', encoding='utf-8-sig') as f:
            reader = csv.reader(f, delimiter=';')
            for row in reader:
                # New Format: word(infinitive);transcription;translations;ex1_en;ex1_ru;...
                if not row or len(row) < 3:
                    continue
                
                # Build examples HTML
                examples_html = []
                # Examples start from index 3
                for i in range(3, len(row) - 1, 2):
                    source = row[i]
                    translation = row[i+1] if i+1 < len(row) else ""
                    
                    if not source and not translation:
                        continue
                        
                    if examples_html:
                        examples_html.append('<div class="example-divider"></div>')
                    
                    examples_html.append(f'<div class="example-item">')
                    examples_html.append(f'  <div class="example-en">{format_text(source)}</div>')
                    examples_html.append(f'  <div class="example-ru">{format_text(translation)}</div>')
                    examples_html.append(f'</div>')
                
                fields = [
                    row[0],             # Word (Front)
                    row[0],             # Infinitive (Back - same as word now)
                    row[1],             # Transcription
                    row[2],             # Translations
                    "".join(examples_html) # Examples_HTML
                ]
                
                note = genanki.Note(model=model, fields=fields)
                deck.add_note(note)
                count += 1
                
        genanki.Package(deck).write_to_file(output_file)
        print(f"Successfully created {output_file} with {count} cards.")
        
    except FileNotFoundError:
        print(f"Error: File {input_file} not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert VocabMaster CSV to Anki .apkg")
    parser.add_argument("input", help="Path to input CSV file")
    parser.add_argument("-o", "--output", help="Path to output .apkg file", default="vocab_deck.apkg")
    parser.add_argument("-n", "--name", help="Anki deck name", default="VocabMaster Deck")
    
    args = parser.parse_args()
    csv_to_apkg(args.input, args.output, args.name)

# Gemini Word Processor

English | [Русский](README.ru.md)

A client-server application for obtaining detailed information about English words and phrases using Google Gemini.

- **Backend**: FastAPI API that processes words via `gemini-cli`
- **Web Client**: React + Vite application with minimal dependencies

## ✨ Features

- Processing of individual words and phrases (e.g., "look for")
- Context support for more accurate translations (e.g., `[a piece of furniture] table`)
- Support for 10 popular languages with language-specific rules:
  - **German nouns**: Automatically includes definite articles and plural forms (e.g., "Apfel" → "der Apfel (die Äpfel)")
  - **English verbs**: Automatically adds the "to" particle (e.g., "go" → "to go")
- Real-time streaming results (asynchronous processing) with concurrency control
- History persistence: selected languages and word history stay after page refresh
- Get transcription (IPA), translation options, and usage examples
- Saving results to a CSV file optimized for **ReWord** (and other apps like Anki)
- Minimal dependency size

## ⚙️ Requirements

- **Python 3.10+**
- **uv** (for managing Python dependencies)
- **Node.js 18+** (for the web client)
- **Gemini CLI**: the `gemini` utility must be installed and available in the PATH (check with `gemini -h`)
- **screen**: required for running servers in the background (Linux only)
  - *Debian/Ubuntu*: `sudo apt install screen`
  - *Fedora*: `sudo dnf install screen`
  - *Arch*: `sudo pacman -S screen`

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/Lowara1243/VocabMaster
cd VocabMaster/
```

### 2. Set up the Python environment

```bash
uv venv
source .venv/bin/activate  # Linux/Mac
# or .venv\Scripts\activate on Windows
```

### 3. Install dependencies

```bash
# Python dependencies (backend)
uv sync

# Frontend dependencies (if using the web client)
cd frontend
npm install
cd ..
```

### 4. Configure environment variables

#### For the web client:

```bash
cp .env.example .env
```

Edit `.env` and specify the API URL:

```bash
VITE_APP_API_URL=http://127.0.0.1:8000/process-words
```

### Option 1: Quick Start (Recommended)

Run the following command to automatically set up dependencies (on first run) and start both backend and frontend:

```bash
chmod +x run_project.sh
./run_project.sh
```

### Option 2: Manual Start

```bash
# Recommended method
uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Or via the helper script
uv run python backend/run.py
```

The server will start on `http://127.0.0.1:8000`

#### Step 2: Start the frontend

In a new terminal:

```bash
cd frontend
npm install
npm run dev
```

Open your browser and go to `http://localhost:5173`

### Usage Examples

1. Enter words separated by commas in the text field.
2. For a more accurate translation, you can specify the context in square brackets, for example: `[a piece of furniture] table`
3. Select the source and target languages
4. Click "Process Words"
5. The results will be displayed in real time
6. The history is automatically saved in the browser
7. Download the CSV using the "Download CSV" button

## 📁 Project Structure

```
.
├── backend/
│   ├── main.py              # FastAPI server
│   └── prompts/             # Prompt templates for Gemini
│       ├── prompt.txt
│       └── fix_json_prompt.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main component
│   │   ├── utils.js         # CSV and formatting
│   │   ├── simple.css       # Minimal CSS
│   │   └── components/
...
│   └── package.json         # Only React + Vite
├── pyproject.toml           # Python dependencies
└── README.md                # This file
```

## 🔧 Configuration

**Backend:**
- `GEMINI_MODEL` - Gemini model (default: gemini-2.5-flash)
- `MAX_CONCURRENT_REQUESTS` - Maximum number of simultaneous requests to Gemini (default: 5).


**Frontend (for production):**
- `VITE_APP_API_URL` - Backend URL (default: http://127.0.0.1:8000/process-words)

## 🎯 CSV Format

The results are saved in a CSV with a `;` delimiter, optimized for direct import into **ReWord**:

| Word | Transcription | Translations | Examples (Source; Translation; ...) |
|-------|--------------|----------|---------------------------------|

Examples contain the word being studied highlighted with `#` symbols for convenient import into ReWord or Anki.

### 🗃️ Anki Support (.apkg)

If you prefer using **Anki**, you can convert the downloaded CSV into a native Anki package (`.apkg`) with custom styling:

```bash
uv run python scripts/csv_to_anki.py result.csv -o my_deck.apkg -n "My English Deck"
```

This will create a deck with a professional layout, transcription, and examples.

## 🧪 Development

```bash
# Formatting and linting
cd frontend
npm run lint

# Production build
npm run build

# Preview production
npm run preview
```

## 📝 Notes

For other project notes, please see the [Specifications document](docs/EN/specifications.md).

## 🔗 Useful Links

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Vite Documentation](https://vitejs.dev/)
- [Gemini CLI](https://github.com/google/generative-ai-cli)

## 📄 License

This project was created for educational purposes.

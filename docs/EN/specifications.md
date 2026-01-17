# Specifications

## 📝 Notes

- The backend **must** use `gemini-cli` via a subprocess (limitation of integration with a Google account)
- CSV files use UTF-8 with BOM for compatibility with Excel
- The web client saves history in the browser's localStorage
- The console client appends results to a single CSV file
- Both clients can work simultaneously with one backend
- When working with different languages, it is necessary to take into account their specific linguistic features (e.g., capitalization of nouns in German, presence of articles, etc.), and to adapt the prompts for `gemini-cli` as needed.
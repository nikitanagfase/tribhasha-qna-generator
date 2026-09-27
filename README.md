# TriBhasha — Multilingual QnA Generator

Upload a PDF / DOCX / TXT document and generate accurate, context-grounded
Question–Answer pairs in **English, Hindi, and Marathi**, exported as a
single `QnA.xlsx` with three sheets (Questions, Answers columns).

## Tech stack
- **UI**: Streamlit
- **LLM**: Groq API (`llama-3.3-70b-versatile`) for both QnA generation and translation
- **Text extraction**: pdfplumber (PDF), python-docx (DOCX), plain read (TXT)
- **Excel export**: pandas + openpyxl
- **Auth**: SQLite + salted PBKDF2 password hashing (simple username/password login & register)

## Project structure
```
tribhasha_qna_generator/
├── .streamlit/
│   └── config.toml         # forces a light theme so text stays readable
│                            # regardless of the user's OS/browser theme
├── assets/
│   ├── logo_full.png        # icon + wordmark — shown on the login screen
│   └── logo_icon.png        # icon only — shown in the sidebar
├── app/
│   ├── extractor.py       # PDF/DOCX/TXT → plain text
│   ├── llm_client.py       # shared Groq client + retry logic
│   ├── qna_generator.py    # text → English QnA pairs (JSON)
│   ├── translator.py       # English QnA → Hindi / Marathi
│   └── excel_writer.py     # QnA pairs → QnA.xlsx (3 sheets)
├── auth/
│   └── database.py         # SQLite login/register
├── streamlit_app.py         # main app (theme, login, workflow)
├── requirements.txt
├── .env.example
└── output/                  # generated files land here if run outside Streamlit
```

## Setup

1. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   venv\Scripts\activate        # Windows
   source venv/bin/activate     # macOS/Linux
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Add your Groq API key**
   - Copy `.env.example` to `.env`
   - Get a free key at https://console.groq.com/keys
   - Paste it into `.env`:
     ```
     GROQ_API_KEY=your_actual_key_here
     ```

4. **Run the app**
   ```bash
   streamlit run streamlit_app.py
   ```
   The app opens at `http://localhost:8501`.

5. **Use it**
   - Register a new account, then log in
   - Upload a `.pdf`, `.docx`, or `.txt` file
   - Pick how many QnA pairs (10–15)
   - Click **Generate QnA**
   - Download `QnA.xlsx`

## Notes
- The first run creates a local `tribhasha_users.db` (SQLite) for login accounts — safe to delete to reset all users.
- If a PDF is scanned/image-only (no selectable text), extraction will fail with a clear error — this system does not perform OCR.
- Every stage (extraction, generation, translation, Excel export) has its own error handling, so a bad file or a flaky API call shows a friendly message instead of crashing the app.

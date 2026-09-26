# Multilingual QnA Generation System

An end-to-end pipeline that extracts content from documents (PDF, DOCX, TXT), automatically generates context-aware Question-Answer pairs, translates them into English, Hindi and Marathi, and exports everything into a single, styled Excel file.



## Author

Nikita Nagfase

## Affiliation

Department of MCA 

Suryodaya College Of Engineering And Technology, Nagpur

## Introduction

Manually reading through documents to create Question-Answer pairs is time-consuming and doing it across multiple languages multiplies the effort further. This project addresses that problem by building an intelligent, automated system that accepts a document in `.pdf`, `.docx`, or `.txt` format, understands its content, and generates meaningful, context-aware QnA pairs from it.

The generated QnA pairs are then translated into three languages — **English, Hindi and Marathi** — and compiled into a single structured Excel file (`QnA.xlsx`), with one dedicated sheet per language. The system also includes a secure Login/Register module, so the tool can be safely used by multiple users and a robust error-handling layer that ensures the pipeline never crashes, even when it encounters invalid files, empty documents, API downtime or malformed responses.

The goal is to provide a reliable, user-friendly tool that turns any English document into ready-to-use multilingual QnA content, useful for education, content localization and assessment generation.

## Project Structure

```
├── app.py
├── auth/
│   └── ...               # Login/Register logic, password hashing, SQLite database
├── pipeline/
│   ├── extractor.py       # PDF/DOCX/TXT text extraction
│   ├── qna_generator.py   # English QnA generation
│   ├── translator.py      # Hindi & Marathi translation
│   └── excel_builder.py   # QnA.xlsx generation with styled sheets
├── requirements.txt
└── README.md
```

## Methodology

### System Flow

```
User Login / Register (SQLite + salted password hashing)
        │
        ▼
Document Upload (.pdf / .docx / .txt)
        │
        ▼
   Text Extraction
        │
        ▼
 English QnA Generation
        │
        ▼
   Hindi Translation
        │
        ▼
  Marathi Translation
        │
        ▼
  Excel File Builder ──► QnA.xlsx (English, Hindi, Marathi sheets)
```

Each stage runs sequentially with a live status indicator (spinner), so the user always knows which step of the pipeline is currently executing.

### Implementation

1. **Authentication Layer** — Users register and log in through a SQLite-backed system. Passwords are never stored in plain text; each password is salted and hashed before being saved and verified securely on login.
2. **Document Ingestion** — Based on the uploaded file's extension, the appropriate extractor is invoked to pull raw text out of the `.pdf`, `.docx` or `.txt` file.
3. **QnA Generation** — The extracted text is passed to an LLM-based generation module, which produces contextually relevant, grammatically correct Question-Answer pairs in English.
4. **Translation** — The English QnA pairs are translated into Hindi and Marathi in two separate steps, preserving the meaning and structure of each question and answer.
5. **Excel Compilation** — All three language sets are written into a single workbook, `QnA.xlsx`, with one sheet per language and styled header rows.
6. **Error Handling** — Every module (extraction, generation, translation, Excel build) is wrapped in exception handling, so invalid files, empty documents, API downtime, rate limits or bad JSON responses surface as friendly error messages instead of crashing the application.

## Features

- **Multi-format input** — Accepts `.pdf`, `.docx`, and `.txt` documents
- **Automated QnA generation** — Extracts meaningful, context-aware Question-Answer pairs from input content
- **Multilingual output** — Auto-translates QnA pairs into **English**, **Hindi**, and **Marathi**
- **Secure authentication** — Login/Register system built on SQLite with salted password hashing (no plain-text passwords ever stored)
- **Full pipeline with live feedback** — Extract → Generate QnA → Translate (Hindi) → Translate (Marathi) → Build Excel, with a spinner/status indicator at every step
- **Robust error handling** — Gracefully handles invalid files, empty documents, API downtime, rate limits and malformed API responses with user-friendly error messages instead of crashing

### Output Format

The final deliverable is a single file: **`QnA.xlsx`**

| Sheet Name | Columns             |
|------------|----------------------|
| English    | Questions, Answers   |
| Hindi      | Questions, Answers   |
| Marathi    | Questions, Answers   |

Each sheet contains styled headers and only the QnA pairs relevant to that language.

## Tech Stack

- **Language:** Python
- **Database:** SQLite (user authentication)
- **Password Security:** Salted hashing (e.g., `bcrypt` / `hashlib` + salt)
- **Document Parsing:** PDF / DOCX / TXT extraction libraries
- **QnA Generation & Translation:** LLM-based API
- **Excel Export:** `openpyxl` / `xlsxwriter`
- **UI (optional):** Streamlit 



## Installation

### Downloaded / Local Setup

1. **Download or clone the repository**

   ```bash
   git clone <your-repo-url>
   cd <your-repo-name>
   ```

   Or download the ZIP from GitHub and extract it locally.

2. **Create a virtual environment (recommended)**

   ```bash
   python -m venv venv
   venv\Scripts\activate      # Windows
   source venv/bin/activate   # macOS/Linux
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables** (API keys, etc.) in a `.env` file if required by your project.

5. **Run the application**

   ```bash
   python app.py
   ```

6. Open the local URL shown in the terminal, register/log in, upload a document, and download the generated `QnA.xlsx`.

## Error Handling

The system handles the following gracefully, without crashing:

- Invalid or corrupted file uploads
- Empty or unreadable documents
- API downtime / connection failures
- API rate limit errors
- Malformed / unexpected API (JSON) responses

Each failure surfaces a clear, user-friendly error message in the UI.

## Notes

- Input documents are expected to be primarily in English, but the pipeline can handle mixed-language content.
- Output strictly follows the required format: single Excel file, 3 sheets, `Questions`/`Answers` columns.


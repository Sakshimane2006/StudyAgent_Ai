# StudyPilot AI — Learn Smarter, Prepare Better

StudyPilot AI is a local-first study assistant for turning your lecture PDFs into searchable notes, grounded AI explanations, chapter revision packs, practice quizzes, and a saved exam plan. It is built with Python, Streamlit, Google's official `google-genai` SDK, PyPDF, NumPy, and SQLite.

## What it does

- **Dashboard:** real counts for indexed PDFs/pages, quiz attempts, and completed tasks.
- **My documents:** validates and extracts text page by page from PDFs up to 20 MB, creates semantic embeddings, tracks source pages, and lets you delete stored notes.
- **AI study chat:** embeds your question, ranks your saved note chunks using NumPy cosine similarity, and answers using the top passages. Retrieved document names and page numbers are shown as sources. English and Hinglish questions are supported.
- **Smart summaries:** creates chapter summaries, definitions, exam notes, and flashcards from an indexed PDF.
- **Quiz practice:** generates validated four-option MCQs with explanations and difficulty levels, scores completed attempts, and saves the history.
- **Study planner:** saves subjects, exam dates, study hours, daily tasks, and task-completion progress in SQLite.
- **My progress:** displays statistics calculated from the database, not sample or fabricated data.

## Privacy and API-key safety

The original PDF is processed in memory and is **not saved** by this app. Extracted text, page references, and embedding vectors are saved in the local SQLite database so search and study features persist between runs. Deleting a document removes its text chunks and embeddings from that database. Your notes and question are sent to the Gemini API when you use an AI feature. Do not upload material you are not allowed to share with that service. The app does not intentionally log API keys or provider error response bodies.

For local use, keep your Gemini API key in `.env`, which is excluded by `.gitignore`. For Streamlit Community Cloud, add it in the app's Secrets settings; the application supports both sources and never needs the key in source code. Never put a real key in `.env.example`, Python source, screenshots, or GitHub. Uploads are size-limited, password-protected PDFs are rejected, and scanned PDFs without selectable text need OCR first. Retrieved document content is treated as untrusted reference material so instructions inside notes do not override the tutor's rules.

## Requirements

- Windows 10/11 (or macOS/Linux), Python 3.10 or newer, and an internet connection for Gemini requests.
- A Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey). Review Google's current API pricing, free-tier limits, and data policies before use.

## Windows: install and run

Open PowerShell in the project folder:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
notepad .env
```

In `.env`, replace the empty value after `GEMINI_API_KEY=` with your **new** key and save the file. Do not add quotes unless your key itself requires them. The file must be named `.env` and sit next to `app.py`; editing `.env.example` does not configure the app. Alternatively, copy `.streamlit\secrets.toml.example` to `.streamlit\secrets.toml` and add the key there. Start the app:

```powershell
python -m streamlit run app.py
```

Streamlit opens the local app in your browser (normally at `http://localhost:8501`). Keep the terminal open while using it. To stop the app, press `Ctrl+C` in that terminal. If PowerShell blocks environment activation, either allow it for your user according to your organization's policy or run the interpreter directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

The default database is created at `data\studypilot.db` the first time the app starts. Set `STUDYPILOT_DB_PATH` in `.env` to store it elsewhere. Existing data remains on this device between app runs.

## Run automated tests

Install the requirements, then run:

```powershell
python -m pytest -q
```

The automated tests use fake Gemini SDK clients for deterministic unit tests; they do not make real API calls and do not prove your API key, account quota, model access, or network connection works.

## Use the features

1. Open **My documents**, choose a text-based course PDF, and select **Upload and index PDF**. The first upload calls Gemini's embedding API. Wait for the success message.
2. In **AI study chat**, choose one document or all documents, ask a question, and review the retrieved source pages. Ask for "simple English" or "Hinglish" when helpful.
3. In **Smart summaries**, select a PDF and create its study pack. The generated material is based on the saved extracted notes; a single summary request is limited to 75,000 characters.
4. In **Quiz practice**, select your notes, enter a subject and difficulty, generate a quiz, answer every question, and submit to save the real result.
5. In **Study planner**, create a subject/exam plan, add dated tasks, and check tasks off as you finish them.
6. Visit **Dashboard** and **My progress** to review actual saved documents, scores, and completed tasks. Delete a PDF from **My documents** to erase its stored text and vectors.

## Troubleshooting

- **"Add GEMINI_API_KEY..."**: verify `.env` is in the project root and contains `GEMINI_API_KEY=your_key`, or that `.streamlit\secrets.toml` contains `GEMINI_API_KEY = "your_key"`; restart Streamlit after changing local secrets. `.env.example` is only a template and is not loaded. Never paste the key into chat or source code.
- **Authentication error:** create/check the key in Google AI Studio and ensure it is available to the Gemini API.
- **Quota or rate limit:** wait before retrying; check the current quota and billing settings associated with your key.
- **Unavailable model:** confirm `GEMINI_MODEL` and `GEMINI_EMBEDDING_MODEL` against the current [Gemini models catalog](https://ai.google.dev/gemini-api/docs/models). Older saved vectors cannot be compared to a different embedding model; delete and re-index those PDFs after changing the embedding model.
- **Connection error:** check internet access and try again.
- **Invalid, locked, or empty PDF:** export a valid, unlocked PDF with selectable text. Scanned image PDFs require OCR before upload.
- **Install errors:** ensure the virtual environment is activated and run `python --version`; use a supported, maintained Python release if a package does not yet support your interpreter.
- **Port already in use:** run `python -m streamlit run app.py --server.port 8502`.
- **Reset local study data:** stop the app and remove the specific `data\studypilot.db` file. This irreversibly removes saved documents, quiz results, plans, and tasks.

## GitHub: publish safely

1. Create a new, empty repository on GitHub.
2. From the project folder, run:

   ```powershell
   git init
   git add app.py core pages components database tests .streamlit requirements.txt .env.example .gitignore README.md
   git status
   ```

3. Confirm `.env`, `.venv`, and `data` are **not** staged. If they are staged, stop and unstage them before continuing.
4. Commit and push (replace the URL with your repository):

   ```powershell
   git commit -m "Build StudyPilot AI study assistant"
   git branch -M main
   git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
   git push -u origin main
   ```

Never commit a real API key, local database, or private course notes.

## Deployment

### Deploy to Streamlit Community Cloud

1. **Secure the API key.** If a real Gemini key was ever saved in a tracked file or pushed to GitHub, revoke it in Google AI Studio and create a fresh key. Removing the text in a later commit does not erase it from Git history.
2. Push the project to GitHub using the safe steps above. Confirm the working tree has no real `.env` or `.streamlit/secrets.toml` file staged or committed. Keep `.env.example` and `.streamlit/secrets.toml.example` as blank/safe templates.
3. Sign in at [share.streamlit.io](https://share.streamlit.io/) with GitHub, choose **Create app**, then select your repository, branch, and `app.py` as the main file.
4. Open **Advanced settings → Secrets** before deploying and paste TOML like this, replacing the placeholder with your newly created key:

   ```toml
   GEMINI_API_KEY = "paste-your-new-key-here"
   GEMINI_MODEL = "gemini-3.6-flash"
   GEMINI_EMBEDDING_MODEL = "gemini-embedding-001"
   ```

   Never paste the real key into a source file, GitHub, or a screenshot. Save the settings and deploy.
5. Open the app's URL from Streamlit. If you change the API key later, update **App settings → Secrets** and reboot the app.

The code reads these Streamlit secrets, so the deployed app will use Gemini without a `.env` file. Streamlit installs dependencies from `requirements.txt`.

### Storage and privacy when deployed

The SQLite database and uploaded-note index are local to the running instance by default. Some hosts replace local storage during restarts or redeploys, so this deployment is suitable for a demonstration, not durable multi-user storage. The app is designed for a single local student's private study library, not shared accounts; a public deployment can expose user data and can incur API usage. Restrict access and use durable, access-controlled storage before deploying for real users.

If you are using a different Streamlit host, add the same settings as environment variables or its secrets configuration; do not commit `.env`.

## Project structure

```text
StudyAgent/
├── app.py
├── core/
│   ├── config.py
│   ├── gemini.py
│   ├── learning.py
│   ├── pdf_processing.py
│   └── rag.py
├── pages/
├── components/
├── database/
│   └── db.py
├── tests/
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## How to explain the RAG design in a demo

When a PDF is added, `pypdf` extracts text with its page number. The app splits each page into overlapping text chunks, asks Gemini's embedding model to turn each chunk into a retrieval-document vector, and saves the text, page, and vector in SQLite. A question is embedded as a retrieval query using the same model. NumPy cosine similarity ranks the stored vectors, and the strongest matching passages are supplied to Gemini as untrusted evidence. The UI shows the actual retrieved pages, so the answer can be checked against the source. This retrieval + generation pipeline is why the chat is genuine RAG rather than a general chatbot.

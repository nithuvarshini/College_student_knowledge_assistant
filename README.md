# College Student Knowledge Assistant (RAG)

A RAG system that answers student queries using official college documents — with citations and no hallucinations.

---

## Project Structure

```
college_rag/
├── main.py                  # FastAPI app (entry point)
├── requirements.txt         # All dependencies
├── documents/               # College documents (add yours here)
│   ├── student_handbook_2025.txt
│   ├── academic_calendar_2025.txt
│   ├── placement_policy_2025.txt
│   ├── fees_scholarships_2025.txt
│   ├── library_rules_2025.txt
│   ├── cse_syllabus_2025.txt
│   └── admin_services_2025.txt
├── src/
│   ├── loader.py            # Loads TXT, PDF, DOCX, HTML
│   ├── chunker.py           # Splits text into overlapping chunks
│   ├── vectorstore.py       # ChromaDB + embeddings
│   ├── generator.py         # HuggingFace flan-t5-base LLM
│   └── rag_pipeline.py      # Orchestrator
└── chroma_db/               # Auto-created: vector index
```

---

## Setup (Python 3.12, Windows)

### Step 1 — Create virtual environment
```powershell
python -m venv venv
venv\Scripts\activate
```

### Step 2 — Install dependencies
```powershell
pip install -r requirements.txt
```
First install downloads ~500MB of models. Just wait for it.

### Step 3 — Start the server
```powershell
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 4 — Open in browser
Swagger UI (interactive): http://127.0.0.1:8000/docs

---

## API Endpoints

| Method | Endpoint    | Description                        |
|--------|-------------|------------------------------------|
| GET    | /           | Health check                       |
| POST   | /query      | Ask a question, get cited answer   |
| POST   | /upload     | Upload a new document              |
| GET    | /stats      | Vector store statistics            |
| POST   | /reindex    | Clear and re-index all documents   |
| GET    | /doc-types  | List valid filter values           |

---

## Example Questions to Test

| Question | doc_type_filter |
|----------|----------------|
| What is the minimum attendance required? | handbook |
| When does the next semester start? | calendar |
| Am I eligible for placement with 1 backlog? | placement |
| What scholarships are available for 2nd year? | fees_scholarships |
| What is the fine for late book return? | library |
| What are the prerequisites for Data Structures? | syllabus |
| How do I get a bonafide certificate? | admin |

---

## Tech Stack

| Component        | Technology                          |
|-----------------|-------------------------------------|
| Embeddings       | all-MiniLM-L6-v2 (90MB)           |
| Vector Database  | ChromaDB                            |
| Search Modes     | Semantic, Keyword, Hybrid           |
| LLM              | google/flan-t5-base (300MB, CPU)   |
| API              | FastAPI + Uvicorn                   |
| Document Loaders | PyMuPDF, python-docx, BeautifulSoup |

# COLLEGE RAG PROJECT - COMPLETE SETUP & RUN GUIDE

# SECTION 1 - ONE TIME SETUP (Do this only once)

1. Open PowerShell inside the college_rag_v2 folder
   - Open the folder in File Explorer
   - Click the address bar, type "powershell", press Enter

2. Create virtual environment
   Command: python -m venv venv

3. Activate virtual environment
   Command: venv\Scripts\activate
   You should see (venv) at the start of the line after this.
   Like this: (venv) PS D:\...\college_rag_v2>

   NOTE: If you get an execution policy error, run this first:
   Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
   Then try activating again.

4. Install all packages
   Command: pip install -r requirements.txt

5. Install Streamlit
   Command: pip install streamlit

   NOTE: This downloads around 500MB. Just wait. Do not close
   the terminal. You only do this once.


# SECTION 2 - RUNNING THE PROJECT (Do this every time)

You need TWO PowerShell terminals open at the same time.
Both must have (venv) active.

--- TERMINAL 1 - FastAPI Backend ---

1. Open PowerShell inside college_rag_v2
2. Activate venv:       venv\Scripts\activate
3. Start the server:    python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
4. Wait until you see:  Application startup complete.

IMPORTANT: Do NOT close this terminal. Keep it running.
First run will download AI models (~400MB). Just wait.

--- TERMINAL 2 - Streamlit UI ---

1. Open a SECOND PowerShell inside college_rag_v2
2. Activate venv:       venv\Scripts\activate
3. Start the UI:        streamlit run app.py
4. Browser will open automatically at http://localhost:8501
   If it doesn't open, go there manually.

# SECTION 3 - ACCESSING THE UIs

Streamlit Chat UI  -->  http://localhost:8501
Swagger API UI     -->  http://127.0.0.1:8000/docs

# SECTION 4 - EXAMPLE QUESTIONS TO TEST

Question: What is the minimum attendance required?
Filter:   handbook

Question: When does the next semester start?
Filter:   calendar

Question: Am I eligible for placement with 1 backlog?
Filter:   placement

Question: What scholarships are available for 2nd year students?
Filter:   fees_scholarships

Question: What is the fine for returning a library book late?
Filter:   library

Question: What are the prerequisites for Data Structures?
Filter:   syllabus

Question: How do I apply for a bonafide certificate?
Filter:   admin

# SECTION 5 - TROUBLESHOOTING

Problem: Cannot connect to the API in Streamlit
Fix:     Terminal 1 is not running or venv is not activated.
         Go to Terminal 1, activate venv, run uvicorn command again.

Problem: (venv) not showing after activation
Fix:     Run this: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
         Then run: venv\Scripts\activate

Problem: pip install fails
Fix:     Make sure (venv) is active first.
         Then run: python.exe -m pip install --upgrade pip
         Then retry: pip install -r requirements.txt

Problem: Startup is very slow
Fix:     Normal on first run. AI models are downloading.
         Wait for "Application startup complete" in Terminal 1.

Problem: Port 8000 already in use
Fix:     Close all terminals and reopen them, then try again.

# QUICK REFERENCE - ALL COMMANDS

python -m venv venv                         (create venv, once)
venv\Scripts\activate                       (activate venv)
pip install -r requirements.txt             (install packages, once)
pip install streamlit                       (install streamlit, once)

python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
                                            (Terminal 1 - backend)

streamlit run app.py                        (Terminal 2 - UI)

http://localhost:8501                       (Streamlit UI)
http://127.0.0.1:8000/docs                 (Swagger UI)
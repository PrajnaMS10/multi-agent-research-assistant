## Multi-Agent Research Assistant (React + FastAPI)

### Prerequisites
- Python 3.10+ (recommended)
- Node.js 18+ (for the React frontend)
- Windows PowerShell (paths below use PowerShell)

### 1) Create and activate a virtual environment

From the project root (`multi-agent-research-assistant`):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run this once (then try again):

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### 2) Install Python dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3) Configure environment variables

Put **`GROQ_API_KEY`** in a `.env` file. The server loads, in order:

1. `multi-agent-research-assistant/.env`
2. Parent folder `.env` (e.g. `Gen-AI Project/.env` if you keep secrets next to the repo)

```env
GROQ_API_KEY="YOUR_GROQ_API_KEY"
```

**Models (Groq Cloud):**

| Agent | Role            | Default model                 |
|-------|-----------------|-------------------------------|
| B     | Summarization   | `llama-3.3-70b-versatile`     |
| C     | Related work    | `qwen/qwen3-32b`              |

Optional overrides:

```env
GROQ_MODEL_SUMMARIZATION="llama-3.3-70b-versatile"
GROQ_MODEL_RELATED_WORK="qwen/qwen3-32b"
```

See [Groq models](https://console.groq.com/docs/models) for current IDs (e.g. `llama-3.1-8b-instant` for faster, cheaper summaries).

### 4) Run the API server

In the activated venv, from the project root:

```powershell
python main.py
```

The API listens on **http://127.0.0.1:8000** (with reload enabled).

### 5) Install and run the React frontend

Open a **second** terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** in your browser. The dev server proxies `/api/*` to the backend on port 8000.

### Troubleshooting
- **Venv activation fails**: Use PowerShell and run the `Set-ExecutionPolicy` command above.
- **Missing Python packages**: Re-run `pip install -r requirements.txt` inside the activated venv.
- **Frontend cannot reach the API**: Ensure `python main.py` is running first; check that nothing else is using port 8000.
- **`npm install` errors**: Use Node 18+; try deleting `frontend/node_modules` and running `npm install` again.

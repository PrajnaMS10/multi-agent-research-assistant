## Multi-Agent Research Assistant (Streamlit)

### Prerequisites
- Python 3.10+ (recommended)
- Windows PowerShell

### 1) Create and activate a virtual environment

From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run this once (then try again):

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### 2) Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3) Configure environment variables

Create a `.env` file in the project root (it should be ignored by git) and set:

```env
GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
GROQ_API_KEY="YOUR_GROQ_API_KEY"
OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
```

### 4) Run the app

Run with the main entrypoint:

```powershell
python main.py
```

To run streamlit

```powershell
streamlit run app.py
```

### Troubleshooting
- **Venv activation fails**: Ensure you are using PowerShell and run the `Set-ExecutionPolicy` command above.
- **Missing packages**: Re-run `pip install -r requirements.txt` inside the activated venv.

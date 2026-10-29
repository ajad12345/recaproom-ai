# Deployment Checklist (Streamlit Community Cloud)

1. `git status` shows no `.env` or `.streamlit/secrets.toml`. Run `pytest -q` (all green).
2. Push to GitHub (`git add .` → `git commit -m "..."` → `git push`).
3. share.streamlit.io → **New app** → pick repo, branch `main`, main file `app.py`.
4. **Advanced settings:** choose Python 3.12 (same as README). Paste secrets in TOML:
   ```toml
   LLM_PROVIDER = "groq"
   GROQ_API_KEY = "your_own_key"
   MODEL_NAME = "a_current_model_name"
   ```
   No key? Leave `LLM_PROVIDER = "demo"` and the app runs in Demo Mode.
5. Deploy. If it fails, read the logs, fix `requirements.txt`/secrets, push again.
6. Test the live URL: sample transcript, empty input, wrong file type, Demo Mode off without a key, export download.
7. Put the URL in README (section 13) and the submission. Open the app before the demo (free apps sleep).

Notes: only the Streamlit app runs on Community Cloud (no Ollama/FastAPI). Files and SQLite are temporary. Model names change: if the provider returns a model error, set `MODEL_NAME` to a current model from the provider docs.

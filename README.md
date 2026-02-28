# Adaptive Investment Strategy Predictor

This repository contains a simple Streamlit app that analyzes stock data and suggests investment actions using either a trained model or a fallback rule.

Quick start (Windows PowerShell)

1. Activate the project's virtual environment (if provided) or create one:

```powershell
# If the provided venv exists
& '.\invest_env\Scripts\Activate.ps1'

# Or create a new one and activate
python -m venv .venv
& '.\.venv\Scripts\Activate.ps1'
```

2. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
# optional dev tools
pip install -r requirements-dev.txt
```

3. Ensure data is available

The app expects `data/SMI.csv`. If you don't have it, run the included fetcher:

```powershell
python "data/models/src/data_fetch.py"
```

This will attempt to download data via `yfinance` or write a placeholder CSV on failure.

4. (Optional) Train a fresh model

```powershell
python data/models/src/train.py --quick --model-path data/models/model.joblib
```

5. Run the Streamlit app

```powershell
streamlit run "app/streamlit_app.py"
```

Open the printed URL (usually http://localhost:8501) in your browser.

Run helper (Windows)

There's a small PowerShell helper that activates the provided virtual environment (or creates one), installs requirements, and launches the app:

```powershell
.\run_app.ps1
```

This is the quickest way on Windows to get the app running.

Troubleshooting

- `git` not found: install Git for Windows (https://git-scm.com/download/win).
- `streamlit` command not found: `pip install streamlit`.
- If `yfinance` fails to download data, `data_fetch.py` will create a placeholder CSV so the app can still run.
- If no model is found in `data/models/`, the app will auto-discover the newest `.joblib` file or fall back to rule-based predictions.

Developer notes

- Unit tests: `pytest -q` (the test suite currently passes).
- Lint/format: `black`, `flake8`, `isort` are suggested dev tools in `requirements-dev.txt`.

If you want, I can also:
- Commit these changes to a branch and prepare a PR (you'll need Git installed locally to push).
- Add a UI control to let users select among discovered models.
- Add CI linting steps.

CI & SMTP integration (optional)

- This repo includes a GitHub Actions workflow at `.github/workflows/ci.yml` that runs the unit tests on push and pull requests.
- If you want to run a protected integration job that performs a real SMTP send (not recommended for normal CI), you can enable the commented `integration` job in that workflow and configure repository secrets.

To add the secrets in GitHub (Repository settings → Secrets → Actions):

1. Open your repository on GitHub and go to Settings → Secrets and variables → Actions → New repository secret.
2. Add the following secrets (example names used by the workflow):
	- `SMTP_HOST` (e.g. `smtp.gmail.com`)
	- `SMTP_PORT` (e.g. `587` or `465`)
	- `SMTP_USER` (your email address)
	- `SMTP_PASS` (app password or SMTP credential)
	- `FROM_EMAIL` (optional)

Once secrets are set, uncomment and enable the `integration` job in `.github/workflows/ci.yml` to run the manual send as a protected job (be cautious — this will send real email).

For local testing and instructions on creating an App Password for Gmail, see `EMAIL_TESTING.md` in the project root.

---

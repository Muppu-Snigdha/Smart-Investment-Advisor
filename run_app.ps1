# Helper PowerShell script to activate a venv and run the Streamlit app
# Usage: .\run_app.ps1

# Prefer provided invest_env, otherwise use .venv
if (Test-Path .\invest_env\Scripts\Activate.ps1) {
    Write-Host "Activating invest_env..."
    & '.\invest_env\Scripts\Activate.ps1'
} else {
    if (-not (Test-Path .\.venv)) {
        Write-Host "Creating .venv..."
        python -m venv .venv
    }
    Write-Host "Activating .venv..."
    & '.\.venv\Scripts\Activate.ps1'
}

Write-Host "Installing runtime requirements (if missing)..."
python -m pip install --upgrade pip
pip install -r requirements.txt

Write-Host "Launching Streamlit app..."
streamlit run "app/streamlit_app.py"

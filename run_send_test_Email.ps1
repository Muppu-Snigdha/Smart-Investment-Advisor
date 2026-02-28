<#
Prompt for SMTP credentials (if not already set in environment) and run the manual email test.

Usage: from repository root in PowerShell:
    & '.\run_send_test_Email.ps1'

The script will not persist secrets to disk. It sets environment variables only for the current session
and invokes the Python script at data/models/tests/send_test_Email.py.
#>

Write-Host "Running manual email test runner..."

# Helper to read secure string and convert to plain
function Read-SecurePlainText($prompt) {
    $secure = Read-Host -AsSecureString $prompt
    $bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try {
        $plain = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)
    } finally {
        [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
    return $plain
}

# Get or prompt for variables
if (-not $env:SMTP_HOST) {
    $env:SMTP_HOST = Read-Host "SMTP host (default smtp.gmail.com)" -DefaultValue "smtp.gmail.com"
}
if (-not $env:SMTP_PORT) {
    $env:SMTP_PORT = Read-Host "SMTP port (465 for SSL or 587 for STARTTLS)" -DefaultValue "587"
}
if (-not $env:SMTP_USER) {
    $env:SMTP_USER = Read-Host "SMTP user (your email address)"
}
if (-not $env:SMTP_PASS) {
    $env:SMTP_PASS = Read-SecurePlainText "SMTP password (App password)"
}
if (-not $env:FROM_EMAIL) {
    $env:FROM_EMAIL = Read-Host "From email (leave blank to use SMTP_USER)" -DefaultValue $env:SMTP_USER
}

Write-Host "Using SMTP_HOST=$($env:SMTP_HOST) SMTP_PORT=$($env:SMTP_PORT) SMTP_USER=$($env:SMTP_USER)"

# Run the python script
python "data/models/tests/send_test_Email.py"

Write-Host "Done."

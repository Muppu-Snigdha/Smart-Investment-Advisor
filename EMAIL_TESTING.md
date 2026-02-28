How to run the manual email send test (Gmail)
============================================

This project includes a manual test runner at `data/models/tests/send_test_Email.py` which calls
`send_notification` in `data/models/email.py` and will attempt to send real email via an SMTP server.

Important: do NOT commit credentials to source control. Use environment variables or a local `.env` file
(which is loaded by `python-dotenv`) for testing only.

Quick steps (Gmail / App Password recommended)
---------------------------------------------

1. Enable 2-Step Verification for the Google account you want to use.
   - Visit https://myaccount.google.com/security and follow the steps under "2-Step Verification".

2. Create an App Password (recommended)
   - On the same Security page choose "App passwords" under "Signing in to Google".
   - Select "Mail" as the app and pick a device (or choose "Other" and name it).
   - Click "Generate" and copy the 16-character password.

3. Configure environment variables for the test (PowerShell, current session only):

```powershell
$env:SMTP_HOST = "smtp.gmail.com"
$env:SMTP_PORT = "587"    # or "465" for SMTPS
$env:SMTP_USER = "your.email@gmail.com"
$env:SMTP_PASS = "<your_app_password_here>"
$env:FROM_EMAIL = "your.email@gmail.com"  # optional
```

4. Run the manual test script from the repository root:

```powershell
# activate venv if needed
& '.\invest_env\Scripts\Activate.ps1'
python "data/models/tests/send_test_Email.py"
```

Notes & troubleshooting
-----------------------
- If you see `SMTPAuthenticationError` with `BadCredentials`, verify the app password is correct and that 2-Step Verification is enabled.
- If you prefer not to use an app password, you can configure OAuth2 or use a transactional email provider (SendGrid, Mailgun, etc.).
- The tests include mocked unit tests (`data/models/tests/test_send_email_mock.py`) so CI and local test runs do not require real SMTP credentials.

Security reminder
-----------------
- Do not paste the app password into issue trackers, commit messages, or chat logs you want to keep public.
- For CI, use the provider's secret store (GitHub Actions secrets, GitLab CI variables, etc.) and never store secrets in the repository.

If you'd like, I can also add a short CI workflow example that runs the mocked tests and shows how to configure secrets for a real send in a protected job.
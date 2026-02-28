import os

# dotenv is optional for tests/environments where it's not installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


def send_notification(to_email, subject, body):
    """Send an email using SendGrid HTTP API.

    Reads SENDGRID_API_KEY from environment. Does a single POST to the SendGrid v3
    Mail Send endpoint. Raises an exception on non-2xx responses.
    """
    api_key = os.getenv("SENDGRID_API_KEY")
    sender = os.getenv("FROM_EMAIL")
    if not api_key:
        print("SENDGRID_API_KEY not set; cannot send via SendGrid.")
        return
    if not sender:
        print("FROM_EMAIL not set; please set FROM_EMAIL environment variable.")
        return

    # Import requests lazily so tests that mock it don't require it at import time
    try:
        import requests
    except Exception as e:
        raise RuntimeError("requests library is required for SendGrid sending") from e

    url = "https://api.sendgrid.com/v3/mail/send"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": sender},
        "subject": subject,
        "content": [{"type": "text/plain", "value": body}],
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=10)
    if resp.status_code >= 400:
        raise RuntimeError(f"SendGrid send failed: {resp.status_code} {resp.text}")

    print("SendGrid: email queued/sent (status)", resp.status_code)

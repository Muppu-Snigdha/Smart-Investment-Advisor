from dotenv import load_dotenv
import os
import smtplib
from email.message import EmailMessage

load_dotenv()

def send_notification(to_email, subject, body):
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", 587))
    user = os.getenv("SMTP_USER")
    pwd  = os.getenv("SMTP_PASS")
    sender = os.getenv("FROM_EMAIL", user)

    if not host or not user or not pwd:
        print("SMTP not configured in .env (SMTP_HOST/SMTP_USER/SMTP_PASS).")
        return

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(host, port) as s:
        s.starttls()
        s.login(user, pwd)
        s.send_message(msg)

    print("Email sent successfully to", to_email)

# ===== TEST run =====
if __name__ == "__main__":
    # replace with your personal email to test
    test_to = "smartinvestmentadvisor36@gmail.com"
    send_notification(test_to, "Test from Smart Investment Advisor", "This is a test email.")
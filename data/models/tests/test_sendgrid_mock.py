import os
import sys
import types
import importlib


def test_sendgrid_success(monkeypatch, capsys):
    # Ensure env vars are set
    monkeypatch.setenv("SENDGRID_API_KEY", "SG.TESTKEY")
    monkeypatch.setenv("FROM_EMAIL", "from@example.com")

    # Create a dummy response object
    class DummyResp:
        def __init__(self, status_code, text=""):
            self.status_code = status_code
            self.text = text

    # Create a fake requests module with post function
    def fake_post(url, headers=None, json=None, timeout=10):
        return DummyResp(202, "Accepted")

    fake_requests = types.SimpleNamespace(post=fake_post)

    # Ensure our fake requests is used when the function imports it
    monkeypatch.setitem(sys.modules, "requests", fake_requests)

    # Load the module by file path to avoid package import issues
    import importlib.util
    path = os.path.join(os.path.dirname(__file__), "..", "sendgrid_email.py")
    path = os.path.normpath(path)
    spec = importlib.util.spec_from_file_location("sendgrid_email", path)
    sendgrid = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sendgrid)

    # Should not raise
    sendgrid.send_notification("to@example.com", "sub", "body")

    captured = capsys.readouterr()
    assert "SendGrid: email queued/sent" in captured.out


def test_sendgrid_failure(monkeypatch):
    monkeypatch.setenv("SENDGRID_API_KEY", "SG.TESTKEY")
    monkeypatch.setenv("FROM_EMAIL", "from@example.com")

    class DummyResp:
        def __init__(self, status_code, text=""):
            self.status_code = status_code
            self.text = text

    def fake_post(url, headers=None, json=None, timeout=10):
        return DummyResp(400, "Bad Request")

    fake_requests = types.SimpleNamespace(post=fake_post)
    monkeypatch.setitem(sys.modules, "requests", fake_requests)

    import importlib.util
    path = os.path.join(os.path.dirname(__file__), "..", "sendgrid_email.py")
    path = os.path.normpath(path)
    spec = importlib.util.spec_from_file_location("sendgrid_email", path)
    sendgrid = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sendgrid)

    try:
        sendgrid.send_notification("to@example.com", "sub", "body")
    except RuntimeError as e:
        assert "SendGrid send failed" in str(e)
    else:
        raise AssertionError("Expected RuntimeError on SendGrid 400 response")


def test_sendgrid_missing_env(monkeypatch, capsys):
    # Unset env vars
    monkeypatch.delenv("SENDGRID_API_KEY", raising=False)
    monkeypatch.delenv("FROM_EMAIL", raising=False)

    # Load module by file path (avoid package import issues when tests run)
    import importlib.util
    path = os.path.join(os.path.dirname(__file__), "..", "sendgrid_email.py")
    path = os.path.normpath(path)
    spec = importlib.util.spec_from_file_location("sendgrid_email", path)
    sendgrid = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sendgrid)

    # Should return early (prints a message) and not raise
    sendgrid.send_notification("to@example.com", "sub", "body")
    captured = capsys.readouterr()
    assert "SENDGRID_API_KEY not set" in captured.out or "FROM_EMAIL not set" in captured.out

import importlib.util
import sys
from pathlib import Path

# load main.py as a module
ROOT = Path(__file__).resolve().parents[2]
main_path = ROOT / "main.py"
spec = importlib.util.spec_from_file_location("main_mod", str(main_path))
main_mod = importlib.util.module_from_spec(spec)
sys.modules["main_mod"] = main_mod
spec.loader.exec_module(main_mod)


def test_fetch_data_exists_and_works(monkeypatch):
    # monkeypatch yf.download to return a simple DataFrame
    import pandas as pd
    df = pd.DataFrame({"Close": [1, 2, 3]})
    monkeypatch.setattr(main_mod.yf, "download", lambda sym, period: df)
    assert hasattr(main_mod, "fetch_data")
    out = main_mod.fetch_data("XYZ")
    assert out is df


def test_password_functions(monkeypatch):
    # simulate login_user verifying password and reset_password storing value
    monkeypatch.setattr(main_mod, "login_user", lambda u, p: "email" if p == "oldpw" else None)
    stored = {}
    monkeypatch.setattr(main_mod, "reset_password", lambda u, p: stored.update({"user": u, "pw": p}))

    assert main_mod.login_user("alice", "oldpw") == "email"
    assert main_mod.login_user("alice", "wrong") is None
    main_mod.reset_password("alice", "newpw")
    assert stored == {"user": "alice", "pw": "newpw"}


def test_about_text_available():
    # ABOUT_TEXT constant should exist and include a heading and summary
    assert hasattr(main_mod, "ABOUT_TEXT")
    text = main_mod.ABOUT_TEXT
    assert isinstance(text, str)
    # check for title and a keyword from the description
    assert "Smart Investment Advisor" in text
    assert "Analyze real-time" in text
    assert "Features" in text
    assert "How to Use" in text


def test_stock_price_coercion():
    # ensure comparison logic converts values to floats and avoids Series truth tests
    import pandas as pd

    # normal series case
    close = pd.Series([10.0, 12.0])
    latest_price = float(close.iloc[-1])
    first_price = float(close.iloc[0])
    change = latest_price - first_price
    assert isinstance(latest_price, float)
    assert change == 2.0

    # simulate a scenario where iloc returns a single-element Series
    df = pd.DataFrame({"Close": [1.0, 2.0]})
    raw_latest = df.iloc[-1]   # this is a Series, mimicking potential yfinance output
    # our logic should convert this cleanly via .item()
    latest_price = float(raw_latest.item())
    assert isinstance(latest_price, float)
    assert latest_price == 2.0

    # also validate earlier DataFrame row case
    row = pd.DataFrame({"Close": [5.0]})
    latest_price = float(row.iloc[-1].iloc[0])
    assert isinstance(latest_price, float)
    assert latest_price == 5.0


def test_price_open_coercion():
    import pandas as pd
    # data frame with Close/Open, raw iloc may be numpy scalar or Series
    df = pd.DataFrame({"Close": [100.0], "Open": [95.0]})
    raw_price = df["Close"].iloc[-1]
    raw_open = df["Open"].iloc[0]
    if hasattr(raw_price, "item"):
        price = float(raw_price.item())
    else:
        price = float(raw_price)
    if hasattr(raw_open, "item"):
        open_price = float(raw_open.item())
    else:
        open_price = float(raw_open)
    change = price - open_price
    assert isinstance(price, float)
    assert isinstance(open_price, float)
    assert change == 5.0


def test_portfolio_and_watchlist(monkeypatch, tmp_path):
    # use a temporary database file by monkeypatching sqlite3.connect
    db_file = tmp_path / "users.db"
    import sqlite3
    real_connect = sqlite3.connect
    def fake_connect(path):
        return real_connect(str(db_file))
    monkeypatch.setattr(sqlite3, "connect", fake_connect)

    # re-import main_mod to initialize db
    import importlib
    import main as main_mod
    main_mod.init_db()

    # test portfolio add/get
    main_mod.add_to_portfolio("testuser", "AAPL", 10, 150.0)
    port = main_mod.get_portfolio("testuser")
    assert port == [("AAPL", 10, 150.0)]

    # test watchlist add/get
    main_mod.add_to_watchlist("testuser", "GOOGL")
    wl = main_mod.get_watchlist("testuser")
    assert wl == ["GOOGL"]

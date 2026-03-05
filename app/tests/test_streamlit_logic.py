import importlib.util
import sys
from pathlib import Path
import pandas as pd
import numpy as np


# Load streamlit_app.py by file path so tests work regardless of package installation
ROOT = Path(__file__).resolve().parents[2]
module_path = ROOT / "app" / "streamlit_app.py"
spec = importlib.util.spec_from_file_location("streamlit_app", str(module_path))
streamlit_app = importlib.util.module_from_spec(spec)
sys.modules["streamlit_app"] = streamlit_app
spec.loader.exec_module(streamlit_app)

predict_strategy = streamlit_app.predict_strategy


def test_fallback_buy_on_positive_return():
    df = pd.DataFrame({
        "Close": [100.0, 101.0]
    }, index=["2025-10-01", "2025-10-02"])
    res = predict_strategy(df, model=None)
    assert res["using_model"] is False
    assert res["recommended_buy"] is True


class FakeModel:
    def predict(self, X):
        # return an array of zeros then a 1 to simulate last positive prediction
        return np.array([0] * (X.shape[0] - 1) + [1])


def test_model_prediction_used_when_available():
    df = pd.DataFrame({
        "Close": [100.0, 102.0],
        "ma5": [99.0, 100.5],
        "ma20": [98.0, 99.5],
        "vol20": [0.01, 0.02],
        "momentum": [0.0, 0.02],
    }, index=["2025-10-01", "2025-10-02"])
    fake = FakeModel()
    res = predict_strategy(df, model=fake)
    assert res["using_model"] is True
    assert res["recommended_buy"] is True
    assert res["model_pred"] == 1


def test_live_ticker_html(monkeypatch):
    # create fake yfinance download output with two days for three tickers
    import pandas as pd
    fake_data = pd.DataFrame(
        {
            "AAPL": [150.0, 152.0],
            "MSFT": [250.0, 249.0],
            "GOOGL": [2800.0, 2810.0],
        },
        index=["2025-01-01", "2025-01-02"],
    )
    class FakeDF:
        def __getitem__(self, key):
            return fake_data
        def iloc(self, *args, **kwargs):
            return fake_data.iloc[args]
    def fake_download(tickers, period, threads):
        # mimic yfinance.download return value: DataFrame with MultiIndex columns
        df = fake_data.copy()
        df.columns = pd.MultiIndex.from_product([["Close"], df.columns])
        return df

    monkeypatch.setattr(streamlit_app.yf, "download", fake_download)
    html = streamlit_app.get_live_ticker_html()
    # should contain the symbols present in our fake data and a colored span
    assert "AAPL" in html
    assert "MSFT" in html
    assert "GOOGL" in html
    assert "span" in html


def test_session_defaults_and_nav(monkeypatch):
    # the module should initialise with landing and home page defaults
    assert "auth_page" in streamlit_app.st.session_state
    # allow either the legacy 'Landing' start page or 'Login' if defaults shifted
    assert streamlit_app.st.session_state.auth_page in ("Landing", "Login")
    assert "nav_page" in streamlit_app.st.session_state
    assert streamlit_app.st.session_state.nav_page == "Home"

    # simulate clicking the About button via the helper
    streamlit_app.st.session_state.nav_page = "Home"
    # simulate query parameters being set by clicking an anchor
    monkeypatch.setattr(streamlit_app.st, "experimental_get_query_params", lambda: {"nav": ["About"]})
    # stub markdown so it doesn't attempt to render during the test
    monkeypatch.setattr(streamlit_app.st, "markdown", lambda *args, **kwargs: None)
    streamlit_app.show_navbar()
    assert streamlit_app.st.session_state.nav_page == "About"

    # ensure Profile link is also recognised
    monkeypatch.setattr(streamlit_app.st, "experimental_get_query_params", lambda: {"nav": ["Profile"]})
    streamlit_app.show_navbar()
    assert streamlit_app.st.session_state.nav_page == "Profile"


def test_landing_page_transition(monkeypatch):
    # verify show_landing_page moves to login when button pressed
    streamlit_app.st.session_state.auth_page = "Landing"
    def fake_button(label, key=None):
        return label == "Get Started"
    monkeypatch.setattr(streamlit_app.st, "button", fake_button)
    monkeypatch.setattr(streamlit_app.st, "rerun", lambda: None)
    recorded = []
    monkeypatch.setattr(streamlit_app.st, "markdown", lambda txt, **kw: recorded.append(txt))
    streamlit_app.show_landing_page()
    assert streamlit_app.st.session_state.auth_page == "Login"
    # landing page should include our new sections
    assert any("Features" in t for t in recorded)
    assert any("How to Use" in t for t in recorded)

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

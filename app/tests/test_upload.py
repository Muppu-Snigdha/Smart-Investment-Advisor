import tempfile
from pathlib import Path
import importlib.util
import sys

# load streamlit_app.py by path
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("streamlit_app", str(ROOT / "app" / "streamlit_app.py"))
streamlit_app = importlib.util.module_from_spec(spec)
sys.modules["streamlit_app"] = streamlit_app
spec.loader.exec_module(streamlit_app)


def test_load_model_from_invalid_file(tmp_path):
    # create a text file and ensure loader returns None (can't load as joblib)
    f = tmp_path / "not_a_model.joblib"
    f.write_text("this is not a joblib file")
    res = streamlit_app.load_model_from_file(f)
    assert res is None

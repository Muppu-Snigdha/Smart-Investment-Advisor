import json
import importlib.util
import sys
from pathlib import Path

# load streamlit_app.py by path (matches other tests in this repo)
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("streamlit_app", str(ROOT / "app" / "streamlit_app.py"))
streamlit_app = importlib.util.module_from_spec(spec)
sys.modules["streamlit_app"] = streamlit_app
spec.loader.exec_module(streamlit_app)

sa = streamlit_app


def test_load_model_metadata_missing_file(tmp_path):
    # Create a fake model file without metadata
    model = tmp_path / "model.joblib"
    model.write_text("fake")
    meta = sa.load_model_metadata(model)
    assert isinstance(meta, dict)
    assert meta["name"] == "model.joblib"
    assert meta["created_at"] is None


def test_load_model_metadata_from_file(tmp_path):
    model = tmp_path / "mymodel.joblib"
    model.write_text("fake")
    meta_path = tmp_path / "mymodel.joblib.meta.json"
    data = {"name": "mymodel", "created_at": "2025-10-18T00:00:00Z", "accuracy": 0.91}
    meta_path.write_text(json.dumps(data))
    meta = sa.load_model_metadata(model)
    assert meta["name"] == "mymodel"
    assert meta["created_at"] == "2025-10-18T00:00:00Z"
    assert meta["accuracy"] == 0.91

import importlib.util
import sys
from pathlib import Path

# load streamlit_app.py by path
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("streamlit_app", str(ROOT / "app" / "streamlit_app.py"))
streamlit_app = importlib.util.module_from_spec(spec)
sys.modules["streamlit_app"] = streamlit_app
spec.loader.exec_module(streamlit_app)

find_models = streamlit_app.find_models


def test_find_models_empty(tmp_path):
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    res = find_models(models_dir)
    assert res == []


def test_find_models_with_files(tmp_path):
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    f1 = models_dir / "a.joblib"
    f2 = models_dir / "b.joblib"
    f1.write_text("x")
    f2.write_text("y")
    res = find_models(models_dir)
    # should return both files
    assert set([p.name for p in res]) == {"a.joblib", "b.joblib"}

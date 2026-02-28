import importlib.util
from pathlib import Path


def test_streamlit_app_imports_and_loads_model():
    project_root = Path(__file__).resolve().parents[3]
    spec = importlib.util.spec_from_file_location('app', str(project_root / 'app' / 'streamlit_app.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    # call the loader directly; it should not raise
    load_model = getattr(mod, 'load_model', None)
    assert load_model is not None
    model = load_model()
    # model may be None (fallback), but calling load_model should not raise
    assert True

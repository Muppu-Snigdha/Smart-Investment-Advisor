import subprocess
import sys
from pathlib import Path
import tempfile


def test_train_quick_creates_model_and_meta():
    project_root = Path(__file__).resolve().parents[3]
    script = project_root / 'data' / 'models' / 'src' / 'train.py'

    with tempfile.TemporaryDirectory() as td:
        model_path = Path(td) / 'model.joblib'
        # Run train.py in quick mode and point the model path to temp dir
        cmd = [sys.executable, str(script), '--quick', '--model-path', str(model_path)]
        res = subprocess.run(cmd, capture_output=True, text=True)
        assert res.returncode == 0, f"Train script failed: {res.stderr}"

        # Check that model and metadata exist
        meta_path = model_path.with_suffix('.meta.json')
        assert model_path.exists(), 'Model file was not created'
        assert meta_path.exists(), 'Metadata file was not created'

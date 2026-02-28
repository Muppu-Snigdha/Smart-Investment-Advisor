import importlib.util
import sys
from pathlib import Path
import traceback

try:
    project_root = Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location('features', str(project_root / 'data' / 'models' / 'src' / 'features.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    import pandas as pd

    csv_path = project_root / 'data' / 'SMI.csv'
    if not csv_path.exists():
        print(f"Data file not found: {csv_path}")
        sys.exit(2)

    # Read raw CSV without forcing date parsing here. The features module will
    # normalize the DataFrame (remove header/meta rows and parse dates). This
    # avoids pandas' element-wise date inference warning for messy CSVs.
    df = pd.read_csv(csv_path)
    print('Original columns:', df.columns.tolist())

    feat = mod.make_features(df)
    print('\nFeatures head:')
    print(feat.head())

    tgt = mod.make_target(df)
    print('\nTarget head:')
    print(tgt.head())

except Exception as e:
    print('Error while running feature checks:')
    traceback.print_exc()
    sys.exit(1)

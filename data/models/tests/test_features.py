import pandas as pd
import numpy as np
import importlib.util
from pathlib import Path


def load_features_module():
    proj = Path(__file__).resolve().parents[3]
    spec = importlib.util.spec_from_file_location('features', str(proj / 'data' / 'models' / 'src' / 'features.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_make_features_on_clean_df():
    mod = load_features_module()
    dates = pd.date_range('2022-01-01', periods=30, freq='D')
    price = pd.Series(100 + (np.arange(30) * 0.5), index=dates)
    df = pd.DataFrame({'Close': price, 'Open': price - 0.5})

    features = mod.make_features(df)
    assert 'return' in features.columns
    assert 'ma5' in features.columns
    assert 'ma20' in features.columns
    assert 'vol20' in features.columns
    assert 'momentum' in features.columns
    assert not features.empty


def test_make_target_on_df_with_header_rows():
    mod = load_features_module()
    # Create a DataFrame that simulates a CSV with a header row before dates
    header = pd.DataFrame([['Price', 'Close', 'High', 'Low', 'Open', 'Volume']], columns=[0,1,2,3,4,5])
    dates = pd.date_range('2022-01-01', periods=10, freq='D')
    price = pd.Series(50 + np.arange(10), index=dates)
    df_clean = pd.DataFrame({'Close': price, 'Open': price - 1})

    # Prepend a fake header row by converting to CSV and reading back (to mimic messy CSV)
    csv = header.to_csv(index=False, header=False) + df_clean.to_csv()
    from io import StringIO
    df_messy = pd.read_csv(StringIO(csv))

    target = mod.make_target(df_messy)
    assert 'target' in target.columns
    assert set(target['target'].unique()).issubset({0,1})

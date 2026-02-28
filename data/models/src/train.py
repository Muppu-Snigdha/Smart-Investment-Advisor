import os
import sys
import json
import subprocess
from datetime import datetime, timezone
import argparse
from pathlib import Path
import pandas as pd
import importlib
import logging

# Dynamic import helpers so the module can be imported even when sklearn/joblib
# are not installed. Training will raise clear errors at runtime if packages missing.
def _dynamic_import(name: str):
	try:
		return importlib.import_module(name)
	except Exception:
		return None

sklearn = _dynamic_import("sklearn")
if sklearn is not None:
	RandomForestClassifier = getattr(_dynamic_import("sklearn.ensemble"), "RandomForestClassifier")
	train_test_split = getattr(_dynamic_import("sklearn.model_selection"), "train_test_split")
	accuracy_score = getattr(_dynamic_import("sklearn.metrics"), "accuracy_score")
else:
	RandomForestClassifier = None
	train_test_split = None
	accuracy_score = None

joblib = _dynamic_import("joblib")

# make sure features module from same folder can be imported when this script is run
sys.path.insert(0, str(Path(__file__).resolve().parent))
from features import make_features, make_target

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def _safe_read_csv(csv_path: Path) -> pd.DataFrame:
	"""Read CSV without forcing date parsing. The features module will normalize dates.

	This avoids pandas' element-wise date inference warning for messy CSVs.
	"""
	return pd.read_csv(csv_path)

def main(argv=None):
	parser = argparse.ArgumentParser(description="Train a simple model on SMI features")
	parser.add_argument("--quick", action="store_true", help="Run a quick training with fewer estimators")
	parser.add_argument("--model-path", type=str, default=None, help="Where to save the model file")
	parser.add_argument("--n-estimators", type=int, default=None, help="Number of trees for RandomForest")
	parser.add_argument("--test-size", type=float, default=0.2, help="Test set fraction")
	args = parser.parse_args(argv)

	project_root = Path(__file__).resolve().parents[3]
	csv_path = project_root / "data" / "SMI.csv"
	zip_path = project_root / "data" / "SMI.csv.zip"

	if not csv_path.exists() and not zip_path.exists():
		raise FileNotFoundError(f"Could not find data file at {csv_path} or {zip_path}")

	# Read CSV safely (no parse_dates here)
	if csv_path.exists():
		logging.info(f"Loading data from {csv_path}")
		raw_df = _safe_read_csv(csv_path)
	else:
		logging.info(f"Loading data from {zip_path}")
		raw_df = _safe_read_csv(zip_path)

	# Create features and target (features module will normalize dates)
	df_feat = make_features(raw_df)
	df_full = make_target(raw_df)

	# Align features & target by index intersection
	df = df_feat.join(df_full['target'], how='inner')

	X = df[["ma5", "ma20", "vol20", "momentum"]]
	y = df["target"].astype(int)

	# Check sklearn availability
	if train_test_split is None or RandomForestClassifier is None or accuracy_score is None:
		raise ImportError("scikit-learn is required to train the model. Install with: python -m pip install scikit-learn")

	X_train, X_test, y_train, y_test = train_test_split(X, y, shuffle=False, test_size=args.test_size)

	# Determine n_estimators: CLI flag takes precedence, then --quick, then default
	if args.n_estimators is not None:
		n_estimators = args.n_estimators
	elif args.quick:
		n_estimators = 5
	else:
		n_estimators = 100

	logging.info(f"Training RandomForest (n_estimators={n_estimators})")
	model = RandomForestClassifier(n_estimators=n_estimators, random_state=42)
	model.fit(X_train, y_train)

	pred = model.predict(X_test)
	acc = float(accuracy_score(y_test, pred))
	logging.info(f"Accuracy: {acc:.4f}")

	if joblib is None:
		raise ImportError("joblib is required to save the model. Install with: python -m pip install joblib")

	model_dir = project_root / "data" / "models"
	model_dir.mkdir(parents=True, exist_ok=True)
	# Determine model filename: if user provided a path, use it; otherwise create a versioned filename
	if args.model_path:
		model_path = Path(args.model_path)
	else:
		ts = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
		short_hash = None
		try:
			short_hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], cwd=str(project_root), text=True).strip()
		except Exception:
			short_hash = None

		name_parts = ["model", ts]
		if short_hash:
			name_parts.append(short_hash)
		fname = ".".join(["_".join(name_parts), "joblib"])  # e.g. model_20251018T070000Z_ab12cd.joblib
		model_path = model_dir / fname

	joblib.dump(model, model_path)
	logging.info(f"Model saved to {model_path}")

	# Save metadata
	# Collect richer metadata: timestamp, git commit (if available), dataset range, and feature stats
	timestamp = datetime.utcnow().isoformat() + 'Z'
	git_hash = None
	try:
		git_hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], cwd=str(project_root), text=True).strip()
	except Exception:
		# Git not available or not a repo — leave git_hash as None
		git_hash = None

	# Dataset date range (use the index of df if datetime-like)
	date_min = None
	date_max = None
	try:
		if hasattr(df.index, 'min'):
			date_min = str(df.index.min())
			date_max = str(df.index.max())
	except Exception:
		date_min = None
		date_max = None

	# Feature statistics
	feature_stats = {}
	try:
		desc = X.describe().to_dict()
		for col in X.columns:
			feature_stats[col] = {
				'mean': float(desc[col]['mean']) if 'mean' in desc[col] else None,
				'std': float(desc[col]['std']) if 'std' in desc[col] else None,
			}
	except Exception:
		feature_stats = {}

	meta = {
		"n_estimators": n_estimators,
		"test_size": args.test_size,
		"accuracy": acc,
		"model_path": str(model_path),
		"timestamp_utc": timestamp,
		"git_short_hash": git_hash,
		"dataset_date_min": date_min,
		"dataset_date_max": date_max,
		"feature_stats": feature_stats,
	}
	meta_path = model_path.with_suffix('.meta.json')
	with open(meta_path, 'w', encoding='utf-8') as f:
		json.dump(meta, f, indent=2)
	logging.info(f"Metadata saved to {meta_path}")


if __name__ == "__main__":
	main()
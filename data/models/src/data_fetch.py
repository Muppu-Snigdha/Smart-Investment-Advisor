from pathlib import Path
import sys
import subprocess
import importlib
import pandas as pd
from typing import Optional


def ensure_package(name: str, import_name: Optional[str] = None) -> Optional[object]:
    """Ensure a python package is importable. If it's missing, try to install it.

    Returns the imported module on success, or None if it could not be imported/installed.
    """
    import_name = import_name or name
    try:
        return importlib.import_module(import_name)
    except Exception:
        try:
            print(f"Package '{name}' not found. Attempting to install...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", name])
            return importlib.import_module(import_name)
        except Exception as exc:
            print(f"Could not install '{name}': {exc}")
            return None


def fetch_history_with_yf(yf_module, ticker: str, period: str = "3y", interval: str = "1d") -> pd.DataFrame:
    """Use a yfinance-like module to download data and return DataFrame.
    Raises RuntimeError on failure.
    """
    try:
        df = yf_module.download(ticker, period=period, interval=interval, progress=False)
    except Exception as exc:
        raise RuntimeError(f"Failed to download data for {ticker}: {exc}") from exc

    if df is None or df.empty:
        raise RuntimeError(f"No data returned for {ticker} (period={period}, interval={interval}).")

    return df.dropna()


def save_dataframe(df: pd.DataFrame, out_path: str) -> None:
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=True)


def write_placeholder(out_path: str) -> None:
    # create a minimal placeholder CSV so downstream code has a file
    cols = ["Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"]
    df = pd.DataFrame(columns=cols)
    save_dataframe(df, out_path)


def main() -> int:
    out = Path("data") / "SMI.csv"

    # Try to ensure yfinance is available. If not, attempt install.
    yf = ensure_package("yfinance")

    if yf is None:
        print("Warning: 'yfinance' unavailable. Writing placeholder CSV instead of real data.")
        try:
            write_placeholder(str(out))
            print(f"⚠️ Placeholder saved to {out}")
            return 0
        except Exception as e:
            print(f"Failed to write placeholder CSV: {e}", file=sys.stderr)
            return 1

    # If we have yfinance, fetch and save real data with error handling
    try:
        df = fetch_history_with_yf(yf, "SMI", period="3y")
        save_dataframe(df, str(out))
        print(f"✅ Data saved successfully to {out}")
        return 0
    except Exception as e:
        print(f"Error fetching data: {e}", file=sys.stderr)
        # Attempt to save placeholder so the file exists
        try:
            write_placeholder(str(out))
            print(f"⚠️ Placeholder saved to {out} after error")
            return 0
        except Exception as e2:
            print(f"Failed to write placeholder after download error: {e2}", file=sys.stderr)
            return 1


if __name__ == "__main__":
    try:
        code = main()
        sys.exit(code)
    except Exception as fatal:
        print(f"Unexpected fatal error: {fatal}", file=sys.stderr)
        # Write a placeholder to avoid leaving downstream users without a file if possible
        try:
            write_placeholder("data/SMI.csv")
        except Exception:
            pass
        sys.exit(1)
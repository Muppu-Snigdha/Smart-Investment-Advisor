import pandas as pd
import warnings


def _select_price_series(df: pd.DataFrame) -> pd.Series:
    """Pick the most appropriate price column from common names."""
    for col in ("Adj Close", "Close", "Close/Last", "Price"):
        if col in df.columns:
            return df[col]
    # If none found, raise to make the failure explicit
    raise KeyError("No recognized price column found. Expected one of: 'Adj Close','Close','Close/Last','Price'.")

def _normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize DataFrame by removing leading header/meta rows and ensuring a datetime index.

    Strategy:
    - If columns are MultiIndex, flatten to last level.
    - Attempt to parse the index as datetimes; if any valid dates exist, trim rows before the
      first valid date and set index to parsed datetimes.
    - Otherwise, attempt to parse the first column as dates and use it as the index (trimming
      leading non-date rows).
    """
    df = df.copy()

    # Flatten multi-index columns if present
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(-1)

    # Try parsing the existing index; prefer a strict ISO-like date at start
    idx_strings = df.index.astype(str).tolist()
    import re

    date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}")
    first_pos = None
    for i, s in enumerate(idx_strings):
        if date_pattern.match(s):
            first_pos = i
            break
        # fallback: if parsing yields a valid datetime
        try:
            if pd.to_datetime(s, errors="coerce") is not pd.NaT:
                if not pd.isna(pd.to_datetime(s, errors="coerce")):
                    first_pos = i
                    break
        except Exception:
            pass

    if first_pos is not None:
        df = df.iloc[first_pos:].copy()
        df.index = pd.to_datetime(df.index.astype(str), errors="coerce")
        df = df.loc[df.index.notna()]
        return df

    # Fallback: try to parse the first column as dates
    if df.shape[1] > 0:
        first_col = df.columns[0]
        # pd.to_datetime may emit a UserWarning when it can't infer a single
        # format for all elements (the CSV contains inconsistent date formatting).
        # That warning is non-fatal and we intentionally fall back to element-
        # wise parsing; suppress the specific warning to keep output clean.
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="Could not infer format")
            parsed_col = pd.to_datetime(df[first_col].astype(str), errors="coerce")
        if parsed_col.notna().any():
            first_pos = parsed_col.notna().argmax()
            df = df.iloc[first_pos:].copy()
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message="Could not infer format")
                df.index = pd.to_datetime(df[first_col].astype(str), errors="coerce")
            # If the first column was just a date label, drop it now
            try:
                df = df.drop(columns=[first_col])
            except Exception:
                pass
            df = df.loc[df.index.notna()]
            return df

    # If we couldn't parse dates, return original
    return df

def make_features(df: pd.DataFrame) -> pd.DataFrame:
    """Return a DataFrame with feature columns added.

    Features added: return (pct change), ma5, ma20, vol20 (20-day std of returns), momentum (20-day).
    """
    df = df.copy()

    # Normalize DataFrame (remove header/meta rows, ensure datetime index, flatten columns)
    df = _normalize_df(df)

    price = _select_price_series(df)
    price = pd.to_numeric(price, errors="coerce")

    # Calculate features
    df["return"] = price.pct_change()
    df["ma5"] = price.rolling(5).mean()
    df["ma20"] = price.rolling(20).mean()
    df["vol20"] = df["return"].rolling(20).std()
    df["momentum"] = price / price.shift(20) - 1

    df = df.dropna()
    return df


def make_target(df: pd.DataFrame) -> pd.DataFrame:
    """Add a binary target column (1 if next-period price goes up, else 0)."""
    df = df.copy()

    # Normalize DataFrame (remove header/meta rows, ensure datetime index, flatten columns)
    df = _normalize_df(df)

    price = _select_price_series(df)
    price = pd.to_numeric(price, errors="coerce")

    df["target"] = ((price.shift(-1) / price - 1) > 0).astype(int)
    df = df.dropna()
    return df

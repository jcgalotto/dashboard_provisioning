import pandas as pd

CATEGORICAL_COLS = ["pri_status", "pri_error_code", "pri_ne_service", "pri_action", "ne_id"]
DATETIME_COL = "pri_action_date"  # ajustar si tu DF usa otra columna temporal


def _ensure_datetime(df: pd.DataFrame) -> pd.DataFrame:
    if DATETIME_COL in df.columns and not pd.api.types.is_datetime64_any_dtype(df[DATETIME_COL]):
        df = df.copy()
        df[DATETIME_COL] = pd.to_datetime(df[DATETIME_COL], errors="coerce")
    return df


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Devuelve una matriz de features tabular para anomalías:
    - Deriva hour/dow/is_weekend desde la columna temporal (si existe)
    - One-hot para categóricas (limitando cardinalidad)
    - No usa pri_message_error como feature (se usa para contexto)
    """
    if df is None or df.empty:
        return pd.DataFrame()

    df = _ensure_datetime(df)
    out = pd.DataFrame(index=df.index)

    # Derivadas temporales
    if DATETIME_COL in df.columns:
        out["hour"] = df[DATETIME_COL].dt.hour.fillna(0).astype(int)
        out["dow"] = df[DATETIME_COL].dt.dayofweek.fillna(0).astype(int)
        out["is_weekend"] = out["dow"].isin([5, 6]).astype(int)
    else:
        out["hour"] = 0
        out["dow"] = 0
        out["is_weekend"] = 0

    # Categóricas -> one-hot
    for col in CATEGORICAL_COLS:
        if col in df.columns:
            safe = df[col].astype(str).str.replace(r"\.0$", "", regex=True).fillna("NA")
            dummies = pd.get_dummies(safe, prefix=col, drop_first=False)
            # Limitar cardinalidad alta
            if dummies.shape[1] > 50:
                tops = safe.value_counts().nlargest(50).index
                safe_clip = safe.where(safe.isin(tops), other="_OTHERS_")
                dummies = pd.get_dummies(safe_clip, prefix=col, drop_first=False)
            out = pd.concat([out, dummies], axis=1)

    return out

import os
import joblib
import pandas as pd
from ml.feature_engineering import build_features

MODEL_PATH = os.path.join("models", "anomaly_isoforest.pkl")


def score_anomalies(df: pd.DataFrame,
                    model_path: str = MODEL_PATH) -> pd.DataFrame:
    """
    Devuelve df con columnas nuevas: anomaly_score (negativo = más raro) y is_anomaly (0/1).
    """
    if df is None or df.empty:
        return pd.DataFrame()

    data = joblib.load(model_path)
    model = data["model"]
    feat_cols = data["feature_columns"]

    X = build_features(df)

    # Alinear columnas esperadas por el modelo
    for c in feat_cols:
        if c not in X.columns:
            X[c] = 0
    X = X[feat_cols]

    scores = model.decision_function(X)  # valores más negativos = más anómalos
    preds = model.predict(X)             # -1 = anomalía, 1 = normal

    out = df.copy()
    out["anomaly_score"] = scores
    out["is_anomaly"] = (preds == -1).astype(int)
    return out

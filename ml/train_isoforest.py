import os
import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest
from ml.feature_engineering import build_features

MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "anomaly_isoforest.pkl")


def train_isoforest(df: pd.DataFrame,
                    n_estimators: int = 300,
                    contamination: float = 0.02,
                    random_state: int = 42) -> str:
    """
    Entrena IsolationForest con features derivados del df.
    contamination: tasa esperada de anomalías (ajustable)
    Retorna la ruta del modelo guardado.
    """
    X = build_features(df)
    if X.empty:
        raise ValueError("No hay datos/feature engineering vacío para entrenar.")

    model = IsolationForest(
        n_estimators=n_estimators,
        contamination=contamination,
        random_state=random_state,
        n_jobs=-1
    )
    model.fit(X)

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump({"model": model, "feature_columns": X.columns.tolist()}, MODEL_PATH)
    return MODEL_PATH

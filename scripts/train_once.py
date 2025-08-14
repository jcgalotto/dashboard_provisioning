import pandas as pd
from ml.train_isoforest import train_isoforest
from services.data_service import get_transacciones
from data.query_builder import build_query
from config.db_config import get_connection

# TODO: completar con tus credenciales o reusar una conexión ya abierta
conn = get_connection("HOST", "1521", "SERVICE", "USER", "PASS")

# TODO: elegir rango histórico
from datetime import datetime
fecha_ini = datetime(2025, 1, 1)
fecha_fin = datetime(2025, 8, 1)

query = build_query(fecha_ini, fecha_fin, ne_id=None, selected_actions=None, selected_services=None)
df = get_transacciones(conn, query)
print("Entrenando con filas:", len(df))
print("Modelo guardado en:", train_isoforest(df, contamination=0.02))


import pandas as pd

def get_transacciones(conn, query):
    return pd.read_sql(query, conn)

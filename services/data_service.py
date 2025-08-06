import pandas as pd


def get_transacciones(conn, query):
    """Retrieve transactions and normalize column names."""
    df = pd.read_sql(query, conn)
    df.columns = df.columns.str.lower()
    return df

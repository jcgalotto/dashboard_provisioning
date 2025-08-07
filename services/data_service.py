import pandas as pd


def get_transacciones(conn, query):
    """Retrieve transactions and normalize column names."""
    df = pd.read_sql(query, conn)
    df.columns = df.columns.str.lower()
    return df


def get_actions(conn, ne_id, services=None):
    """Retrieve distinct actions for a given NE ID and optional services."""
    query = (
        "SELECT DISTINCT pri_action FROM swp_provisioning_interfaces "
        "WHERE pri_ne_id = :ne_id"
    )
    params = {"ne_id": ne_id}
    if services:
        formatted_services = "', '".join(services)
        query += f" AND pri_ne_service IN ('{formatted_services}')"
    df = pd.read_sql(query, conn, params=params)
    df.columns = df.columns.str.lower()
    return df["pri_action"].tolist()


def get_services(conn, ne_id):
    """Retrieve distinct NE services available for a given NE ID."""
    query = (
        "SELECT DISTINCT pri_ne_service FROM swp_provisioning_interfaces "
        "WHERE pri_ne_id = :ne_id"
    )
    df = pd.read_sql(query, conn, params={"ne_id": ne_id})
    df.columns = df.columns.str.lower()
    return df["pri_ne_service"].tolist()

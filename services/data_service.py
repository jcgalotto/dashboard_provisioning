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


def get_realtime_transacciones(conn, start_time, ne_id=None, ne_group=None):
    """Retrieve real-time transactions since ``start_time``."""
    query = (
        "SELECT pri_ne_id, pri_ne_group, pri_status, pri_error_code, pri_action_date "
        "FROM swp_provisioning_interfaces "
        "WHERE pri_action_date >= TO_DATE(:start_time, 'DD-MM-YYYY HH24:MI:SS')"
    )
    params = {"start_time": start_time.strftime("%d-%m-%Y %H:%M:%S")}
    if ne_id:
        query += " AND pri_ne_id = :ne_id"
        params["ne_id"] = ne_id
    if ne_group:
        query += " AND pri_ne_group = :ne_group"
        params["ne_group"] = ne_group
    df = pd.read_sql(query, conn, params=params)
    df.columns = df.columns.str.lower()
    return df

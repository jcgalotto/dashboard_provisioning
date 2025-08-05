
import cx_Oracle
import streamlit as st


def build_dsn(host, port, service_name):
    """Construye un DSN utilizando los parámetros de conexión."""
    return cx_Oracle.makedsn(host, int(port), service_name=service_name)


def get_connection(host, port, service_name, user, password):
    """Abre una conexión utilizando los datos proporcionados."""
    try:
        dsn = build_dsn(host, port, service_name)
        if "db_conn" in st.session_state:
            st.session_state["db_conn"].close()
        st.session_state["db_conn"] = cx_Oracle.connect(user, password, dsn)
        return st.session_state["db_conn"]
    except cx_Oracle.Error as e:
        st.error(f"Error de conexión: {e}")
        return None

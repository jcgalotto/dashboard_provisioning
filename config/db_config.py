
import cx_Oracle
import streamlit as st

def get_connection(host, port, service_name, user, password):
    try:
        dsn = cx_Oracle.makedsn(host, port, service_name=service_name)
        if "db_conn" in st.session_state:
            st.session_state["db_conn"].close()
        st.session_state["db_conn"] = cx_Oracle.connect(user, password, dsn)
        return st.session_state["db_conn"]
    except cx_Oracle.Error as e:
        st.error(f"Error de conexión: {e}")
        return None

import streamlit as st
import pandas as pd
import datetime
from streamlit_autorefresh import st_autorefresh
from services.data_service import get_realtime_transacciones

st.set_page_config(page_title="Operaciones en tiempo real")
st.markdown(
    """
    <style>
    div[data-testid='stSidebarNav'] { display: none; }
    [data-testid='stHeader'] { display: none; }
    </style>
    """,
    unsafe_allow_html=True,
)
st.title("⚡ Operaciones en tiempo real")

if "db_conn" not in st.session_state:
    st.warning("🔌 No hay conexión activa")
    st.stop()

ne_id = st.text_input("NE ID", value=st.session_state.get("rt_ne_id", ""))
ne_group = st.text_input("NE Group", value=st.session_state.get("rt_ne_group", ""))

col1, col2 = st.columns(2)
with col1:
    if st.button("Iniciar"):
        st.session_state["rt_running"] = True
        st.session_state["rt_start_time"] = datetime.datetime.now()
        st.session_state["rt_ne_id"] = ne_id
        st.session_state["rt_ne_group"] = ne_group
with col2:
    if st.button("Detener"):
        st.session_state["rt_running"] = False

running = st.session_state.get("rt_running", False)
start_time = st.session_state.get("rt_start_time")

if running and start_time:
    st_autorefresh(interval=5000, key="rt_refresh")
    df = get_realtime_transacciones(
        st.session_state["db_conn"],
        start_time,
        ne_id or None,
        ne_group or None,
    )
    st.session_state["rt_df"] = df
else:
    df = st.session_state.get("rt_df", pd.DataFrame())

if df.empty:
    st.info("Sin operaciones")
else:
    if "pri_error_code" in df.columns:
        df["pri_error_code"] = df["pri_error_code"].astype("Int64")

    status_counts = df["pri_status"].value_counts()
    total = int(len(df))
    pendiente = int(status_counts.get("K", 0) + status_counts.get("T", 0) + status_counts.get("PENDING", 0))
    ok = int(status_counts.get("O", 0))
    error = int(status_counts.get("E", 0))

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total", total)
    k2.metric("Pendiente", pendiente)
    k3.metric("OK", ok)
    k4.metric("Error", error)

    estados = ["Todos"] + sorted(df["pri_status"].dropna().unique())
    estado = st.selectbox("Estado", estados)
    df_filtrado = df if estado == "Todos" else df[df["pri_status"] == estado]

    if estado == "E":
        errores = ["Todos"] + sorted(df_filtrado["pri_error_code"].dropna().unique())
        error_sel = st.selectbox("Código de error", errores)
        if error_sel != "Todos":
            df_filtrado = df_filtrado[df_filtrado["pri_error_code"] == error_sel]

    st.dataframe(df_filtrado)

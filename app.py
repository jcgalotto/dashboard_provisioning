import streamlit as st
from config.db_config import get_connection
from data.query_builder import build_query
from services.data_service import get_transacciones, get_actions, get_services
from visualizations.charts import (
    kpi_cards,
    status_pie_chart,
    error_detail_bar_chart,
)
from utils.helpers import normalize_error_message
import datetime
import pandas as pd

try:
    from st_aggrid import AgGrid
    HAS_AGGRID = True
except ImportError:
    HAS_AGGRID = False

st.set_page_config(page_title="Dashboard Provisioning", layout="wide")
st.markdown(
    """
    <style>
    div[data-testid='stSidebarNav'] { display: none; }
    [data-testid='stHeader'] { display: none; }
    </style>
    """,
    unsafe_allow_html=True,
)
st.title("📊 Dashboard Provisioning")

# Configuración de conexión
with st.sidebar:
    st.header("🔐 Conexión Oracle")
    host = st.text_input("Host")
    port = st.text_input("Puerto")
    service_name = st.text_input("Service Name")
    user = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")
    if st.button("Conectar"):
        conn = get_connection(host, port, service_name, user, password)
        if conn:
            st.session_state["connection_name"] = f"{host}:{port}/{service_name}"
            st.session_state["db_conn"] = conn
            st.success(f"✅ Conectado a {st.session_state['connection_name']}")
        else:

            st.error("❌ Error al conectar")


# Mostrar log de conexión
if "db_conn" not in st.session_state:
    st.warning("🔌 No hay conexión activa")
    st.stop()

if "connection_name" in st.session_state:
    st.info(f"🔗 Conectado a: {st.session_state['connection_name']}")


# Parámetros de fecha
now = datetime.datetime.now()
col1, col2, col3 = st.columns(3)
with col1:
    fecha_ini_fecha = st.date_input("Fecha Inicio", value=now.date())
    fecha_ini_hora = st.time_input("Hora Inicio", value=datetime.time(0, 0))
    fecha_ini = datetime.datetime.combine(fecha_ini_fecha, fecha_ini_hora)
with col2:
    fecha_fin_fecha = st.date_input("Fecha Fin", value=now.date())
    fecha_fin_hora = st.time_input("Hora Fin", value=now.time())
    fecha_fin = datetime.datetime.combine(fecha_fin_fecha, fecha_fin_hora)
with col3:
    ne_id = st.text_input("NE ID")
    selected_services = selected_actions = None

    if ne_id:
        if "db_conn" not in st.session_state:
            st.warning("🔌 No hay conexión activa")
            st.stop()
        services = get_services(st.session_state["db_conn"], ne_id)
        selected_services = st.multiselect("Servicio", services)
        if selected_services:
            actions = get_actions(
                st.session_state["db_conn"], ne_id, selected_services
            )
            selected_actions = st.multiselect("Acción", actions)
comparar = st.checkbox("Comparar con otro periodo")
if comparar:
    col4, col5 = st.columns(2)
    with col4:
        cmp_ini_fecha = st.date_input(
            "Fecha Inicio Comparación",
            value=fecha_ini_fecha,
            key="cmp_ini_fecha",
        )
        cmp_ini_hora = st.time_input(
            "Hora Inicio Comparación",
            value=datetime.time(0, 0),
            key="cmp_ini_hora",
        )
        fecha_ini_cmp = datetime.datetime.combine(cmp_ini_fecha, cmp_ini_hora)
    with col5:
        cmp_fin_fecha = st.date_input(
            "Fecha Fin Comparación",
            value=fecha_fin_fecha,
            key="cmp_fin_fecha",
        )
        cmp_fin_hora = st.time_input(
            "Hora Fin Comparación",
            value=fecha_fin_hora,
            key="cmp_fin_hora",
        )
        fecha_fin_cmp = datetime.datetime.combine(cmp_fin_fecha, cmp_fin_hora)
else:
    fecha_ini_cmp = fecha_fin_cmp = None

# Ejecutar consulta
if "db_conn" not in st.session_state:
    st.warning("🔌 No hay conexión activa")
    st.stop()
query = build_query(
    fecha_ini,
    fecha_fin,
    ne_id or None,
    selected_actions or None,
    selected_services or None,
)

if "db_conn" not in st.session_state:
    st.warning("🔌 No hay conexión activa")
    st.stop()
df = get_transacciones(st.session_state["db_conn"], query)
st.session_state["transacciones_df"] = df

if comparar:
    query_cmp = build_query(
        fecha_ini_cmp,
        fecha_fin_cmp,
        ne_id or None,
        selected_actions or None,
        selected_services or None,
    )
    df_cmp = get_transacciones(st.session_state["db_conn"], query_cmp)
else:
    query_cmp = ""
    df_cmp = pd.DataFrame()

# Logs detallados
st.write("📋 Log de ejecución")
st.code(query, language="sql")
st.success(f"Total de transacciones recuperadas: {len(df)}")

if comparar:
    st.write("📋 Log de ejecución - Periodo comparación")
    st.code(query_cmp, language="sql")
    st.success(
        f"Total de transacciones periodo comparación: {len(df_cmp)}"
    )

# KPIs
kpi_cards(df)

if st.button("Ver detalle de transacciones"):
    st.switch_page("pages/detalle_transacciones.py")

# Pie chart
st.plotly_chart(status_pie_chart(df), use_container_width=True)

# Gráfico de errores
if not df[df['pri_status'] == 'E'].empty:
    st.subheader("📉 Códigos de Error")
    st.plotly_chart(error_detail_bar_chart(df), use_container_width=True)

if comparar:
    st.subheader("📊 Comparativo de transacciones")

    def resumen(df_base):
        errores = df_base[df_base["pri_status"] == "E"].copy()
        errores["pri_message_error"] = errores["pri_message_error"].apply(
            normalize_error_message
        )
        return (
            errores.groupby(["pri_error_code", "pri_message_error"])
            .size()
            .reset_index(name="cantidad")
        )

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Periodo Actual**")
        st.metric("Operaciones", len(df))
        resumen_actual = resumen(df)
        if not resumen_actual.empty:
            st.dataframe(resumen_actual)
        else:
            st.write("Sin errores")
    with col_b:
        st.markdown("**Periodo Comparación**")
        st.metric("Operaciones", len(df_cmp))
        resumen_cmp = resumen(df_cmp)
        if not resumen_cmp.empty:
            st.dataframe(resumen_cmp)
        else:
            st.write("Sin errores")

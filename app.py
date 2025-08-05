import streamlit as st
from config.db_config import get_connection
from data.query_builder import build_query
from services.data_service import get_transacciones
from visualizations.charts import kpi_cards, status_pie_chart, error_bar_chart
import datetime

st.set_page_config(page_title="Dashboard Provisioning", layout="wide")
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
        st.session_state["connection_name"] = f"{host}:{port}/{service_name}"
        conn = get_connection(host, port, service_name, user, password)
        if conn:
            st.success(f"✅ Conectado a {st.session_state['connection_name']}")

# Mostrar log de conexión
if "connection_name" in st.session_state:
    st.info(f"🔗 Conectado a: {st.session_state['connection_name']}")
else:
    st.warning("🔌 No hay conexión activa")
    st.stop()

# Parámetros de fecha
col1, col2 = st.columns(2)
with col1:
    fecha_ini = st.datetime_input("Fecha Inicio", value=datetime.datetime.now().replace(hour=0, minute=0))
with col2:
    fecha_fin = st.datetime_input("Fecha Fin", value=datetime.datetime.now())

# Ejecutar consulta
query = build_query(fecha_ini, fecha_fin)
df = get_transacciones(st.session_state["db_conn"], query)

# Logs detallados
st.write("📋 Log de ejecución")
st.code(query, language="sql")
st.success(f"Total de transacciones recuperadas: {len(df)}")

# KPIs
kpi_cards(df)

# Pie chart
st.plotly_chart(status_pie_chart(df), use_container_width=True)

# Gráfico de errores
if not df[df['pri_status'] == 'E'].empty:
    st.subheader("📉 Códigos de Error")
    st.plotly_chart(error_bar_chart(df), use_container_width=True)

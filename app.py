import streamlit as st
from config.db_config import get_connection
from data.query_builder import build_query
from services.data_service import get_transacciones, get_actions, get_services
from visualizations.charts import kpi_cards, status_pie_chart, error_bar_chart
import datetime
from dateutil.relativedelta import relativedelta

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


# Filtro de comparación temporal
comparar = st.checkbox("Comparar con periodo anterior")
fecha_ini_prev = fecha_fin_prev = None
if comparar:
    col_cmp1, col_cmp2 = st.columns(2)
    with col_cmp1:
        cantidad = st.number_input("Cantidad", min_value=1, value=1, step=1)
    with col_cmp2:
        unidad = st.selectbox("Unidad", ["Horas", "Días", "Meses", "Años"])
    if unidad == "Horas":
        delta = datetime.timedelta(hours=cantidad)
    elif unidad == "Días":
        delta = datetime.timedelta(days=cantidad)
    elif unidad == "Meses":
        delta = relativedelta(months=cantidad)
    else:
        delta = relativedelta(years=cantidad)
    fecha_ini_prev = fecha_ini - delta
    fecha_fin_prev = fecha_fin - delta


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

query_prev = None
df_prev = None
if fecha_ini_prev and fecha_fin_prev:
    query_prev = build_query(
        fecha_ini_prev,
        fecha_fin_prev,
        ne_id or None,
        selected_actions or None,
        selected_services or None,
    )

df = get_transacciones(st.session_state["db_conn"], query)
if query_prev:
    df_prev = get_transacciones(st.session_state["db_conn"], query_prev)
st.session_state["transacciones_df"] = df

# Logs detallados
st.write("📋 Log de ejecución")
st.code(query, language="sql")
if query_prev:
    st.code(query_prev, language="sql")

if df_prev is not None:
    st.success(
        f"Total de transacciones recuperadas: {len(df)} (previo: {len(df_prev)})"
    )
else:
    st.success(f"Total de transacciones recuperadas: {len(df)}")

# KPIs
kpi_cards(df, df_prev)

if st.button("Ver detalle de transacciones"):
    st.switch_page("pages/detalle_transacciones.py")

# Pie chart
st.plotly_chart(status_pie_chart(df), use_container_width=True)

# Gráfico de errores
if not df[df['pri_status'] == 'E'].empty:
    st.subheader("📉 Códigos de Error")
    st.plotly_chart(error_bar_chart(df), use_container_width=True)

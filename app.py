import streamlit as st
import datetime
import pandas as pd
import plotly.express as px

from config.db_config import get_connection
from data.query_builder import build_query
from services.data_service import get_transacciones, get_actions, get_services
from visualizations.charts import (
    kpi_cards,
    error_comparison_bar_chart,
    realtime_operations_chart,
)
from utils.helpers import normalize_error_message

try:
    from streamlit_autorefresh import st_autorefresh
    HAS_AUTOREFRESH = True
except Exception:
    HAS_AUTOREFRESH = False

st.set_page_config(page_title="Dashboard Provisioning", layout="wide")
st.markdown(
    """
<style>
[data-testid='stSidebarNav'] { display: none; }
[data-testid='stHeader'] { display: none; }
:root { --card-bg: #111418; --panel-bg:#0c0f13; --pill:#132538; }
.block-container { padding-top: 1rem; }
.kpi-card { background: var(--card-bg); border-radius: 16px; padding: 16px; box-shadow: 0 1px 0 #1f2937; }
.topbar { background: var(--pill); padding: 10px 14px; border-radius: 12px; display:flex; align-items:center; gap:12px; }
.pill { padding:6px 10px; border-radius: 999px; background:#0f172a; color:#cbd5e1; font-size:0.9rem; }
</style>
""",
    unsafe_allow_html=True,
)

# --- Sidebar -----------------------------------------------------------------
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
            st.session_state["db_conn"] = conn
            st.session_state["connection_name"] = f"{host}:{port}/{service_name}"
            st.success(f"✅ Conectado a {st.session_state['connection_name']}")
        else:
            st.error("❌ Error al conectar")

    st.header("⏱️ Actualización")
    auto_refresh = st.checkbox("Auto-actualizar", value=False)
    intervalo = st.number_input("Intervalo (segundos)", min_value=5, value=60, step=5)
    if auto_refresh:
        if HAS_AUTOREFRESH:
            st_autorefresh(interval=int(intervalo * 1000), key="data_refresh")
        else:
            st.warning("Instala streamlit-autorefresh para habilitar esta opción")

# --- Top bar -----------------------------------------------------------------
connection_name = st.session_state.get("connection_name", "Desconectado")
connected = "db_conn" in st.session_state
status_color = "#16a34a" if connected else "#4b5563"
st.markdown(
    f"<div class='topbar'><h1 style='margin:0;flex:1'>Dashboard Provisioning</h1>"
    f"<span class='pill' style='background:{status_color}'>{connection_name}</span></div>",
    unsafe_allow_html=True,
)

# --- Stop if no connection ----------------------------------------------------
if not connected:
    st.warning("🔌 No hay conexión activa")
    st.page_link("pages/operaciones_tiempo_real.py", label="⚡ Operaciones en tiempo real", icon="⚡")
    st.stop()

# --- Filters ------------------------------------------------------------------
now = datetime.datetime.now()
with st.form("filtros"):
    col1, col2, col3 = st.columns(3)
    with col1:
        fecha_ini_fecha = st.date_input("Fecha Inicio", value=now.date())
        fecha_ini_hora = st.time_input("Hora Inicio", value=datetime.time(0, 0))
    with col2:
        fecha_fin_fecha = st.date_input("Fecha Fin", value=now.date())
        fecha_fin_hora = st.time_input("Hora Fin", value=now.time())
    with col3:
        ne_id = st.text_input("NE ID")
        selected_services = selected_actions = None
        if ne_id:
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
    submit = st.form_submit_button("Consultar")

st.page_link("pages/operaciones_tiempo_real.py", label="⚡ Operaciones en tiempo real", icon="⚡")

if submit:
    st.session_state["run_query"] = True

if not st.session_state.get("run_query"):
    st.info("Complete los filtros y presione Consultar para obtener datos")
    st.stop()

fecha_ini = datetime.datetime.combine(fecha_ini_fecha, fecha_ini_hora)
fecha_fin = datetime.datetime.combine(fecha_fin_fecha, fecha_fin_hora)
if comparar:
    fecha_ini_cmp = datetime.datetime.combine(cmp_ini_fecha, cmp_ini_hora)
    fecha_fin_cmp = datetime.datetime.combine(cmp_fin_fecha, cmp_fin_hora)
else:
    fecha_ini_cmp = fecha_fin_cmp = None

if not ne_id:
    st.warning("Debe ingresar NE ID")
    st.stop()

# --- Query execution ---------------------------------------------------------
query = build_query(
    fecha_ini,
    fecha_fin,
    ne_id or None,
    selected_actions or None,
    selected_services or None,
)

df = get_transacciones(st.session_state["db_conn"], query)
st.session_state["transacciones_df"] = df
st.caption(f"Última actualización: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

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

# --- Row 1: KPI cards --------------------------------------------------------
def render_kpi_card(title: str, value: str, delta: str | None = None) -> None:
    delta_html = f"<div style='font-size:0.9rem;color:#9ca3af'>{delta}</div>" if delta else ""
    st.markdown(
        f"""
<div class='kpi-card'>
  <div style='font-size:0.9rem;color:#9ca3af'>{title}</div>
  <div style='font-size:2rem;font-weight:700'>{value}</div>
  {delta_html}
</div>
""",
        unsafe_allow_html=True,
    )

total = len(df)
delta_total = None
if comparar and len(df_cmp) > 0:
    delta_val = (total - len(df_cmp)) / len(df_cmp) * 100
    delta_total = f"{delta_val:+.1f}%"
performance = (len(df[df["pri_status"] == "O"]) / total * 100) if total else 0
errores = len(df[df["pri_status"] == "E"])

kpi_row = st.container()
with kpi_row:
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_kpi_card("Total transacciones", f"{total}", delta_total)
    with c2:
        render_kpi_card("Nuevas", "Pendiente")
    with c3:
        render_kpi_card("Performance", f"{performance:.2f}%")
    with c4:
        render_kpi_card("Errores", f"{errores}")

with st.expander("KPIs (legacy)"):
    kpi_cards(df)

# --- Row 2: Charts -----------------------------------------------------------
row2 = st.container()
with row2:
    col1, col2 = st.columns(2)
    with col1:
        def transacciones_time_chart(df_base: pd.DataFrame, start: datetime.datetime, end: datetime.datetime):
            if df_base.empty or "pri_action_date" not in df_base.columns:
                st.info("No data")
                return px.Figure()
            df_ts = df_base.assign(pri_action_date=pd.to_datetime(df_base["pri_action_date"]))
            freq = "H" if (end - start) <= datetime.timedelta(days=1) else "D"
            df_ts = (
                df_ts.groupby(pd.Grouper(key="pri_action_date", freq=freq))
                .size()
                .reset_index(name="cantidad")
            )
            title = "Transacciones por hora" if freq == "H" else "Transacciones por día"
            return px.line(
                df_ts,
                x="pri_action_date",
                y="cantidad",
                labels={"pri_action_date": "Fecha", "cantidad": "Transacciones"},
                title=title,
            )

        st.plotly_chart(
            transacciones_time_chart(df, fecha_ini, fecha_fin),
            use_container_width=True,
        )
    with col2:
        error_mode = st.checkbox("Modo errores")

        def resumen(df_base: pd.DataFrame) -> pd.DataFrame:
            errores_df = df_base[df_base["pri_status"] == "E"].copy()
            if errores_df.empty:
                return pd.DataFrame(
                    columns=["pri_error_code", "pri_message_error", "cantidad"]
                )
            errores_df["pri_message_error"] = errores_df["pri_message_error"].apply(
                normalize_error_message
            )
            return (
                errores_df.groupby(["pri_error_code", "pri_message_error"])
                .size()
                .reset_index(name="cantidad")
            )

        if error_mode:
            resumen_actual = resumen(df)
            if comparar:
                resumen_cmp = resumen(df_cmp)
                fig_err = error_comparison_bar_chart(resumen_actual, resumen_cmp)
                st.plotly_chart(fig_err, use_container_width=True)
            else:
                if resumen_actual.empty:
                    st.info("No hay errores")
                else:
                    fig_err = px.bar(
                        resumen_actual,
                        x="pri_error_code",
                        y="cantidad",
                        color="pri_message_error",
                        labels={
                            "pri_error_code": "Código",
                            "cantidad": "Cantidad",
                            "pri_message_error": "Descripción",
                        },
                        title="Errores por código",
                    )
                    st.plotly_chart(fig_err, use_container_width=True)
        else:
            if df.empty or "pri_status" not in df.columns:
                st.info("No data")
            else:
                status_counts = (
                    df["pri_status"].value_counts().reset_index()
                    if not df.empty
                    else pd.DataFrame({"index": [], "pri_status": []})
                )
                status_counts.columns = ["pri_status", "cantidad"]
                fig_status = px.bar(
                    status_counts,
                    x="pri_status",
                    y="cantidad",
                    labels={"pri_status": "Estado", "cantidad": "Cantidad"},
                    title="Transacciones por estado",
                )
                st.plotly_chart(fig_status, use_container_width=True)

# --- Row 3: Error messages chart ---------------------------------------------
error_row = st.container()
with error_row:
    st.subheader("📊 Errores por mensaje")
    resumen_actual_full = resumen(df)
    if resumen_actual_full.empty:
        st.info("No hay errores")
    else:
        top_actual = (
            resumen_actual_full.groupby("pri_message_error")["cantidad"]
            .sum()
            .reset_index()
            .sort_values("cantidad", ascending=False)
        )
        if comparar and not df_cmp.empty:
            resumen_cmp_full = resumen(df_cmp)
            top_cmp = (
                resumen_cmp_full.groupby("pri_message_error")["cantidad"]
                .sum()
                .reset_index()
            )
            merged = (
                top_actual.merge(
                    top_cmp, on="pri_message_error", how="left", suffixes=("_actual", "_cmp")
                )
                .fillna(0)
                .sort_values("cantidad_actual", ascending=False)
                .head(10)
            )
            merged_long = merged.melt(
                id_vars="pri_message_error",
                value_vars=["cantidad_actual", "cantidad_cmp"],
                var_name="Periodo",
                value_name="Cantidad",
            )
            merged_long["Periodo"] = merged_long["Periodo"].map(
                {"cantidad_actual": "Periodo Actual", "cantidad_cmp": "Periodo Comparación"}
            )
            fig_msg = px.bar(
                merged_long,
                y="pri_message_error",
                x="Cantidad",
                color="Periodo",
                orientation="h",
                labels={"pri_message_error": "Mensaje", "Cantidad": "Transacciones"},
                title="Top errores por mensaje",
            )
            st.plotly_chart(fig_msg, use_container_width=True)
        else:
            top_actual = top_actual.head(10)
            fig_msg = px.bar(
                top_actual,
                y="pri_message_error",
                x="cantidad",
                orientation="h",
                labels={"pri_message_error": "Mensaje", "cantidad": "Transacciones"},
                title="Top errores por mensaje",
            )
            st.plotly_chart(fig_msg, use_container_width=True)

# --- Row 4: Logs -------------------------------------------------------------
log_row = st.container()
with log_row:
    st.subheader("📋 Log de ejecución")
    st.code(query, language="sql")
    st.write(f"Total de transacciones recuperadas: {len(df)}")
    if comparar:
        st.code(query_cmp, language="sql")
        st.write(f"Total de transacciones periodo comparación: {len(df_cmp)}")

# --- Navigation --------------------------------------------------------------
nav = st.container()
with nav:
    st.page_link(
        "pages/detalle_transacciones.py",
        label="📄 Ver detalle de transacciones",
    )
    st.page_link(
        "pages/operaciones_tiempo_real.py",
        label="⚡ Operaciones en tiempo real",
        icon="⚡",
    )

if __name__ == "__main__":
    st.write("Use 'streamlit run app.py'")

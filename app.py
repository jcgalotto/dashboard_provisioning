
import streamlit as st
import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from config.db_config import get_connection
from data.query_builder import build_query
from services.data_service import get_transacciones, get_actions, get_services
from visualizations.charts import kpi_cards, error_comparison_bar_chart
from utils.helpers import normalize_error_message

PALETTE = ["#FF7F50", "#F4A261", "#E9C46A", "#2A9D8F", "#264653"]
px.defaults.template = "plotly_dark"
px.defaults.color_discrete_sequence = PALETTE

try:
    from streamlit_autorefresh import st_autorefresh
    HAS_AUTOREFRESH = True
except Exception:
    HAS_AUTOREFRESH = False

st.set_page_config(page_title="Dashboard Provisioning", layout="wide")
st.markdown("""
<style>
/* Ocultar header y nav nativos */
[data-testid='stHeader'], [data-testid='stSidebarNav'] { display: none; }
.block-container { padding-top: 0.8rem; }

/* Topbar y tarjetas */
.topbar { background: #24304A; border-radius: 12px; padding: 12px 16px; display:flex; gap:12px; align-items:center; }
.pill-ok { background:#17472E; color:#CFF6DF; padding:4px 10px; border-radius:999px; }
.pill-bad { background:#472222; color:#F6CFD0; padding:4px 10px; border-radius:999px; }
.card { background:#2B3040; border-radius:16px; padding:16px; box-shadow:0 1px 0 rgba(255,255,255,0.05); }
.kpi h1 { margin:0; font-size:2rem; }
.kpi small { opacity:.8 }

/* Botones */
.stButton>button { border-radius:10px; }

/* Tablas */
.dataframe th, .dataframe td { color:#EAEAEA !important; }
</style>
""", unsafe_allow_html=True)


def _prepare_error_counts_by_message(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=["pri_message_error", "count"])
    req = {"pri_status", "pri_message_error"}
    if not req.issubset(df.columns):
        return pd.DataFrame(columns=["pri_message_error", "count"])
    err = df[df["pri_status"] == "E"].copy()
    if err.empty:
        return pd.DataFrame(columns=["pri_message_error", "count"])
    err["pri_message_error"] = err["pri_message_error"].astype(str).fillna("").apply(normalize_error_message)
    g = (err.groupby("pri_message_error").size().reset_index(name="count").sort_values("count", ascending=False))
    return g


def _prep_error_code_counts(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=["pri_error_code_str", "pri_message_error_norm", "count"])
    req = {"pri_status", "pri_error_code", "pri_message_error"}
    if not req.issubset(df.columns):
        return pd.DataFrame(columns=["pri_error_code_str", "pri_message_error_norm", "count"])
    err = df[df["pri_status"] == "E"].copy()
    if err.empty:
        return pd.DataFrame(columns=["pri_error_code_str", "pri_message_error_norm", "count"])

    err["pri_error_code_str"] = err["pri_error_code"].astype(str).str.replace(r"\.0$", "", regex=True)
    err["pri_message_error_norm"] = err["pri_message_error"].astype(str).fillna("").apply(normalize_error_message)

    counts = (err.groupby("pri_error_code_str").size().reset_index(name="count").sort_values("count", ascending=False))
    top_msg = (err.groupby(["pri_error_code_str","pri_message_error_norm"]).size()
                 .reset_index(name="n")
                 .sort_values(["pri_error_code_str","n"], ascending=[True, False])
                 .drop_duplicates(subset=["pri_error_code_str"]))
    return counts.merge(top_msg[["pri_error_code_str","pri_message_error_norm"]], on="pri_error_code_str", how="left")


def error_codes_bar(df_actual: pd.DataFrame,
                    df_cmp: pd.DataFrame | None = None,
                    top_n: int = 10,
                    full: bool = False) -> go.Figure:
    cur = _prep_error_code_counts(df_actual)
    cmp_df = _prep_error_code_counts(df_cmp)

    if cur.empty and cmp_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data available", x=0.5, y=0.5, showarrow=False, xref="paper", yref="paper")
        fig.update_layout(height=520 if full else 440, margin=dict(l=10, r=10, t=40, b=10))
        return fig

    if full:
        labels = cur["pri_error_code_str"].tolist() if not cur.empty else cmp_df["pri_error_code_str"].tolist()
    else:
        labels = (cur["pri_error_code_str"].head(top_n).tolist()
                  if not cur.empty else cmp_df["pri_error_code_str"].head(top_n).tolist())

    s_actual = cur.set_index("pri_error_code_str").reindex(labels)["count"].fillna(0).astype(int)
    s_cmp = None
    if not cmp_df.empty:
        s_cmp = cmp_df.set_index("pri_error_code_str").reindex(labels)["count"].fillna(0).astype(int)

    msg_map = cur.set_index("pri_error_code_str")["pri_message_error_norm"].to_dict()
    hovertext = [f"Código: {code}<br>Mensaje: {msg_map.get(code, '')}<br>Transacciones: {int(s_actual.get(code,0))}" for code in labels]

    fig = go.Figure()
    fig.add_trace(go.Bar(y=labels, x=s_actual.values, name="Periodo actual",
                         orientation="h", hovertext=hovertext, hoverinfo="text+x"))
    if s_cmp is not None:
        fig.add_trace(go.Bar(y=labels, x=s_cmp.values, name="Periodo comparación", orientation="h"))

    fig.update_layout(
        barmode="group",
        height=520 if full else 440,
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis_title="Transacciones",
        yaxis_title="Código de error",
        yaxis=dict(type="category"),
        legend=dict(orientation="h", y=-0.15),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#EAEAEA'
    )
    return fig


def error_messages_bar(df_actual: pd.DataFrame,
                       df_cmp: pd.DataFrame | None = None,
                       top_n: int = 10) -> go.Figure:
    cur = _prepare_error_counts_by_message(df_actual)
    cmp_df = _prepare_error_counts_by_message(df_cmp) if df_cmp is not None else pd.DataFrame()
    if cur.empty and (df_cmp is None or cmp_df.empty):
        fig = go.Figure()
        fig.add_annotation(text="No data available", x=0.5, y=0.5, showarrow=False, xref="paper", yref="paper")
        fig.update_layout(height=360, margin=dict(l=10, r=10, t=30, b=10))
        return fig
    labels = cur["pri_message_error"].head(top_n).tolist() if not cur.empty else cmp_df["pri_message_error"].head(top_n).tolist()
    s_actual = cur.set_index("pri_message_error").reindex(labels)["count"].fillna(0).astype(int)
    s_cmp = None
    if not cmp_df.empty:
        s_cmp = cmp_df.set_index("pri_message_error").reindex(labels)["count"].fillna(0).astype(int)

    fig = go.Figure()
    fig.add_trace(go.Bar(y=labels, x=s_actual.values, name="Periodo actual", orientation="h"))
    if s_cmp is not None:
        fig.add_trace(go.Bar(y=labels, x=s_cmp.values, name="Periodo comparación", orientation="h"))
    fig.update_layout(barmode="group", height=500, margin=dict(l=10, r=10, t=40, b=10),
                      xaxis_title="Transacciones", yaxis_title="Mensaje de error (normalizado)",
                      legend=dict(orientation="h", y=-0.15),
                      plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='#EAEAEA')
    return fig


def _resumen_errores(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=["pri_error_code", "pri_message_error", "cantidad"])
    err = df[df["pri_status"] == "E"].copy()
    if err.empty:
        return pd.DataFrame(columns=["pri_error_code", "pri_message_error", "cantidad"])
    err["pri_message_error"] = err["pri_message_error"].astype(str).fillna("").apply(normalize_error_message)
    return err.groupby(["pri_error_code", "pri_message_error"]).size().reset_index(name="cantidad")


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
            st.success("✅ Conectado")
        else:
            st.error("❌ Error al conectar")

    st.header("⏱️ Actualización")
    auto_refresh = st.checkbox("Auto-actualizar", value=True)
    intervalo = st.number_input("Intervalo (segundos)", min_value=5, value=60, step=5)
    st.button("Reset filtros", on_click=lambda: st.session_state.clear())
    if auto_refresh and HAS_AUTOREFRESH:
        st_autorefresh(interval=int(intervalo*1000), key="data_refresh")
    elif auto_refresh and not HAS_AUTOREFRESH:
        st.warning("⚠️ Falta 'streamlit-autorefresh'")


st.title("📊 Dashboard Provisioning")
con_name = st.session_state.get("connection_name", None)
st.markdown(f"<div class='topbar'>Conectado a: "
            f"<span class='{'pill-ok' if con_name else 'pill-bad'}'>{con_name or 'Sin conexión'}</span>"
            f"</div>", unsafe_allow_html=True)

if "db_conn" not in st.session_state:
    st.warning("🔌 No hay conexión activa")
    st.page_link("pages/operaciones_tiempo_real.py", label="⚡ Operaciones en tiempo real", icon="⚡")
    st.stop()


now = datetime.datetime.now()
with st.form("filtros"):
    col1, col2, col3 = st.columns(3)
    with col1:
        fecha_ini_fecha = st.date_input("Fecha inicio", value=now.date())
        fecha_ini_hora = st.time_input("Hora inicio", value=datetime.time(0,0))
    with col2:
        fecha_fin_fecha = st.date_input("Fecha fin", value=now.date())
        fecha_fin_hora = st.time_input("Hora fin", value=now.time())
    with col3:
        ne_id = st.text_input("NE ID")
    with st.expander("Filtros avanzados"):
        selected_services = selected_actions = None
        if ne_id:
            services = get_services(st.session_state["db_conn"], ne_id)
            selected_services = st.multiselect("Servicio", services)
            if selected_services:
                actions = get_actions(st.session_state["db_conn"], ne_id, selected_services)
                selected_actions = st.multiselect("Acción", actions)
        comparar = st.checkbox("Comparar con otro periodo")
        if comparar:
            col4, col5 = st.columns(2)
            with col4:
                cmp_ini_fecha = st.date_input("Fecha inicio comparación", value=fecha_ini_fecha)
                cmp_ini_hora = st.time_input("Hora inicio comparación", value=datetime.time(0,0))
            with col5:
                cmp_fin_fecha = st.date_input("Fecha fin comparación", value=fecha_fin_fecha)
                cmp_fin_hora = st.time_input("Hora fin comparación", value=fecha_fin_hora)
    submitted = st.form_submit_button("Consultar")

if not submitted and "run_query" not in st.session_state:
    st.info("Complete los filtros y presione Consultar para obtener datos")
    st.stop()

if submitted:
    st.session_state["run_query"] = True

fecha_ini = datetime.datetime.combine(fecha_ini_fecha, fecha_ini_hora)
fecha_fin = datetime.datetime.combine(fecha_fin_fecha, fecha_fin_hora)
if 'comparar' in locals() and comparar:
    fecha_ini_cmp = datetime.datetime.combine(cmp_ini_fecha, cmp_ini_hora)
    fecha_fin_cmp = datetime.datetime.combine(cmp_fin_fecha, cmp_fin_hora)
else:
    comparar = False
    fecha_ini_cmp = fecha_fin_cmp = None

if not ne_id:
    st.warning("Debe ingresar NE ID")
    st.stop()

query = build_query(fecha_ini, fecha_fin, ne_id, selected_actions, selected_services)
df = get_transacciones(st.session_state["db_conn"], query)
if comparar:
    query_cmp = build_query(fecha_ini_cmp, fecha_fin_cmp, ne_id, selected_actions, selected_services)
    df_cmp = get_transacciones(st.session_state["db_conn"], query_cmp)
else:
    query_cmp = ""
    df_cmp = pd.DataFrame()

kpi_cards(df)

col1, col2 = st.columns(2)
with col1:
    if df.empty or "pri_action_date" not in df.columns:
        st.info("No data available")
    else:
        df_ts = df.assign(pri_action_date=pd.to_datetime(df["pri_action_date"]))
        freq = "H" if (fecha_fin - fecha_ini) <= datetime.timedelta(days=1) else "D"
        df_ts = df_ts.groupby(pd.Grouper(key="pri_action_date", freq=freq)).size().reset_index(name="cantidad")
        title = "Transacciones por hora" if freq == "H" else "Transacciones por día"
        fig_time = px.line(df_ts, x="pri_action_date", y="cantidad", labels={"pri_action_date":"Fecha", "cantidad":"Transacciones"}, title=title)
        st.plotly_chart(fig_time, use_container_width=True)
with col2:
    if df.empty or "pri_status" not in df.columns:
        st.info("No data available")
    else:
        status_counts = df["pri_status"].value_counts().reset_index()
        status_counts.columns = ["pri_status", "cantidad"]
        fig_status = px.bar(status_counts, x="pri_status", y="cantidad", labels={"pri_status":"Estado", "cantidad":"Transacciones"}, title="Transacciones por estado", color="pri_status", color_discrete_sequence=PALETTE)
        st.plotly_chart(fig_status, use_container_width=True)

st.subheader("🧱 Errores por código (Top N / Completo)")
c1, c2 = st.columns([3,1])
with c1:
    top_n_codes = st.slider("Top N códigos", 5, 30, 10, key="top_err_codes")
with c2:
    ver_completo = st.toggle("Ver completo", value=False)

fig_err_codes = error_codes_bar(df, df_cmp if comparar else None, top_n=top_n_codes, full=ver_completo)
st.plotly_chart(fig_err_codes, use_container_width=True)

map_cur = _prep_error_code_counts(df)[["pri_error_code_str", "pri_message_error_norm", "count"]].rename(
    columns={"pri_error_code_str":"pri_error_code", "count":"count_actual"}
)
if comparar and not df_cmp.empty:
    map_cmp = _prep_error_code_counts(df_cmp)[["pri_error_code_str","count"]].rename(
        columns={"pri_error_code_str":"pri_error_code", "count":"count_cmp"}
    )
    table = map_cur.merge(map_cmp, on="pri_error_code", how="left")
else:
    table = map_cur.copy()

table = table.fillna({"count_actual":0, "count_cmp":0}).sort_values("count_actual", ascending=False)
st.dataframe(table, use_container_width=True)

csv_bytes = table.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Descargar tabla (CSV)", data=csv_bytes, file_name="errores_por_codigo.csv", mime="text/csv")

with st.expander("Ver errores por mensaje (Top 10)"):
    st.plotly_chart(error_messages_bar(df, df_cmp if comparar else None, top_n=10), use_container_width=True)

if comparar and not df_cmp.empty:
    resumen_actual = _resumen_errores(df)
    resumen_cmp = _resumen_errores(df_cmp)
    with st.expander("Comparación de códigos de error entre periodos"):
        st.plotly_chart(error_comparison_bar_chart(resumen_actual, resumen_cmp), use_container_width=True)

st.caption(f"Última actualización: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.write("📋 Log de ejecución")
st.code(query, language="sql")
if comparar and query_cmp:
    st.code(query_cmp, language="sql")

with st.expander("KPIs (vista legacy)"):
    kpi_cards(df)

st.page_link("pages/operaciones_tiempo_real.py", label="⚡ Operaciones en tiempo real", icon="⚡")
st.page_link("pages/detalle_transacciones.py", label="📄 Ver detalle de transacciones")
st.page_link("pages/deteccion_anomalias.py", label="🧭 Detección de anomalías", icon="🧭")

if __name__ == "__main__":
    st.write("Use 'streamlit run app.py'")

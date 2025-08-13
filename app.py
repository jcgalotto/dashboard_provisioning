import streamlit as st
import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from config.db_config import get_connection
from data.query_builder import build_query
from services.data_service import get_transacciones, get_actions, get_services
# Import placeholders (realtime chart linked as página)
from utils.helpers import normalize_error_message

# Paleta común para todos los gráficos
PALETTE = ["#FF7F50", "#F4A261", "#E9C46A", "#2A9D8F", "#264653"]
px.defaults.template = "plotly_dark"
px.defaults.color_discrete_sequence = PALETTE

try:
    from streamlit_autorefresh import st_autorefresh
    HAS_AUTOREFRESH = True
except Exception:
    HAS_AUTOREFRESH = False


# --- Errores por código: helpers y gráfico ---


def _prepare_error_code_counts(df: pd.DataFrame) -> pd.DataFrame:
    """
    Devuelve DataFrame con columnas:
    pri_error_code | pri_message_error_norm | count
    Filtra pri_status == 'E' y normaliza pri_message_error.
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=["pri_error_code", "pri_message_error_norm", "count"])

    required = {"pri_status", "pri_error_code", "pri_message_error"}
    if not required.issubset(set(df.columns)):
        return pd.DataFrame(columns=["pri_error_code", "pri_message_error_norm", "count"])

    err = df[df["pri_status"] == "E"].copy()
    if err.empty:
        return pd.DataFrame(columns=["pri_error_code", "pri_message_error_norm", "count"])

    err["pri_message_error_norm"] = (
        err["pri_message_error"].astype(str).fillna("").apply(normalize_error_message)
    )
    # conversión del código a string sin decimales
    err["pri_error_code_str"] = (
        err["pri_error_code"].astype(str).str.replace(r"\.0$", "", regex=True)
    )
    # conteo por código
    counts = (
        err.groupby("pri_error_code_str", dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
    )
    # mensaje más frecuente por código (normalizado)
    top_msg = (
        err.groupby(["pri_error_code_str", "pri_message_error_norm"])
        .size()
        .reset_index(name="n")
        .sort_values(["pri_error_code_str", "n"], ascending=[True, False])
        .drop_duplicates(subset=["pri_error_code_str"])
        .rename(columns={"n": "msg_freq"})
    )
    out = counts.merge(
        top_msg[["pri_error_code_str", "pri_message_error_norm"]],
        on="pri_error_code_str",
        how="left",
    )
    out = out.rename(columns={"pri_error_code_str": "pri_error_code"})
    return out


def _most_frequent_message_per_code(df: pd.DataFrame) -> pd.DataFrame:
    """
    Devuelve mapping único por pri_error_code -> pri_message_error_norm (más frecuente).
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=["pri_error_code", "pri_message_error_norm"])
    base = _prepare_error_code_counts(df)
    return base[["pri_error_code", "pri_message_error_norm"]].drop_duplicates()


def error_codes_bar(
    df_actual: pd.DataFrame,
    df_cmp: pd.DataFrame | None = None,
    top_n: int = 10,
    full: bool = False,
) -> go.Figure:
    """Barras horizontales por ``pri_error_code``.
    Si ``df_cmp`` está presente añade serie de comparación.
    """

    def _prep_counts(df: pd.DataFrame | None) -> pd.DataFrame:
        if df is None or df.empty:
            return pd.DataFrame(
                columns=["pri_error_code_str", "pri_message_error_norm", "count"]
            )
        err = df[df["pri_status"] == "E"].copy()
        if err.empty:
            return pd.DataFrame(
                columns=["pri_error_code_str", "pri_message_error_norm", "count"]
            )
        err["pri_error_code_str"] = (
            err["pri_error_code"].astype(str).str.replace(r"\.0$", "", regex=True)
        )
        err["pri_message_error_norm"] = (
            err["pri_message_error"].astype(str).fillna("").apply(normalize_error_message)
        )
        counts = (
            err.groupby("pri_error_code_str", dropna=False)
            .size()
            .reset_index(name="count")
            .sort_values("count", ascending=False)
        )
        msg_map = (
            err.groupby(["pri_error_code_str", "pri_message_error_norm"])
            .size()
            .reset_index(name="n")
            .sort_values(["pri_error_code_str", "n"], ascending=[True, False])
            .drop_duplicates(subset=["pri_error_code_str"])
        )
        return counts.merge(
            msg_map[["pri_error_code_str", "pri_message_error_norm"]],
            on="pri_error_code_str",
            how="left",
        )

    cur = _prep_counts(df_actual)
    cmp_df = _prep_counts(df_cmp) if df_cmp is not None else pd.DataFrame()

    if full:
        labels = (
            cur["pri_error_code_str"].tolist()
            if not cur.empty
            else cmp_df["pri_error_code_str"].tolist()
        )
    else:
        labels = (
            cur["pri_error_code_str"].head(top_n).tolist()
            if not cur.empty
            else cmp_df["pri_error_code_str"].head(top_n).tolist()
        )

    s_actual = (
        cur.set_index("pri_error_code_str").reindex(labels)["count"].fillna(0).astype(int)
    )
    s_cmp = (
        cmp_df.set_index("pri_error_code_str").reindex(labels)["count"].fillna(0).astype(int)
        if not cmp_df.empty
        else None
    )

    msg_map = cur.set_index("pri_error_code_str")[
        "pri_message_error_norm"
    ].to_dict()
    hovertext = [
        f"Código: {code}<br>Mensaje: {msg_map.get(code, '')}<br>Transacciones: {s_actual.get(code, 0)}"
        for code in labels
    ]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=labels,
            x=s_actual.values,
            name="Periodo actual",
            orientation="h",
            hovertext=hovertext,
            hoverinfo="text+x",
            marker_color=PALETTE[0],
        )
    )
    if s_cmp is not None:
        hovertext_cmp = [
            f"Código: {code}<br>Mensaje: {msg_map.get(code, '')}<br>Transacciones: {s_cmp.get(code, 0)}"
            for code in labels
        ]
        fig.add_trace(
            go.Bar(
                y=labels,
                x=s_cmp.values,
                name="Periodo comparación",
                orientation="h",
                hovertext=hovertext_cmp,
                hoverinfo="text+x",
                marker_color=PALETTE[2],
            )
        )

    fig.update_layout(
        barmode="group",
        height=520 if full else 440,
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis_title="Transacciones",
        yaxis_title="Código de error",
        yaxis=dict(type="category"),
        legend=dict(orientation="h", y=-0.15),
    )
    return fig


def resumen(df_base: pd.DataFrame) -> pd.DataFrame:
    errores_df = df_base[df_base["pri_status"] == "E"].copy()
    if errores_df.empty:
        return pd.DataFrame(columns=["pri_error_code", "pri_message_error", "cantidad"])
    errores_df["pri_message_error"] = errores_df["pri_message_error"].apply(
        normalize_error_message
    )
    return (
        errores_df.groupby(["pri_error_code", "pri_message_error"])
        .size()
        .reset_index(name="cantidad")
    )

st.set_page_config(page_title="Dashboard Provisioning", layout="wide")
st.markdown(
    """
<style>
[data-testid='stSidebarNav'] { display: none; }
[data-testid='stHeader'] { display: none; }
.block-container { padding-top: 0rem; }
.kpi-card{background:#2B3040;border-radius:12px;padding:16px;box-shadow:0 2px 6px rgba(0,0,0,0.2);}
.topbar{background:#FF7F50;color:#EAEAEA;padding:10px 16px;border-radius:8px;display:flex;justify-content:space-between;align-items:center;}
.status-pill{padding:4px 10px;border-radius:999px;font-size:0.9rem;color:#EAEAEA;}
.status-pill.ok{background:#16a34a;}
.status-pill.bad{background:#dc2626;}
button{transition:filter 0.3s;}
button:hover{filter:brightness(1.1);}
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
pill_class = "ok" if connected else "bad"
st.markdown(
    f"<div class='topbar'><span style='font-size:1.4rem;font-weight:600'>Dashboard Provisioning</span>"
    f"<span class='status-pill {pill_class}'>{connection_name}</span></div>",
    unsafe_allow_html=True,
)

# --- Stop if no connection ----------------------------------------------------
if not connected:
    st.warning("🔌 No hay conexión activa")
    st.page_link("pages/operaciones_tiempo_real.py", label="⚡ Operaciones en tiempo real", icon="⚡")
    st.stop()

# --- Filters ------------------------------------------------------------------
now = datetime.datetime.now()
st.subheader("Filtros")
with st.form("filtros"):
    col1, col2, col3 = st.columns(3)
    with col1:
        fecha_ini_fecha = st.date_input("Fecha Inicio", value=now.date(), key="fecha_ini_fecha")
        fecha_ini_hora = st.time_input("Hora Inicio", value=datetime.time(0, 0), key="fecha_ini_hora")
    with col2:
        fecha_fin_fecha = st.date_input("Fecha Fin", value=now.date(), key="fecha_fin_fecha")
        fecha_fin_hora = st.time_input("Hora Fin", value=now.time(), key="fecha_fin_hora")
    with col3:
        ne_id = st.text_input("NE ID", key="ne_id")
    with st.expander("Filtros avanzados"):
        selected_services = selected_actions = None
        if ne_id:
            services = get_services(st.session_state["db_conn"], ne_id)
            selected_services = st.multiselect("Servicio", services, key="servicio")
            if selected_services:
                actions = get_actions(st.session_state["db_conn"], ne_id, selected_services)
                selected_actions = st.multiselect("Acción", actions, key="accion")
        comparar = st.checkbox("Comparar con otro periodo", key="comparar")
        if comparar:
            col4, col5 = st.columns(2)
            with col4:
                cmp_ini_fecha = st.date_input("Fecha Inicio Comparación", value=fecha_ini_fecha, key="cmp_ini_fecha")
                cmp_ini_hora = st.time_input("Hora Inicio Comparación", value=datetime.time(0, 0), key="cmp_ini_hora")
            with col5:
                cmp_fin_fecha = st.date_input("Fecha Fin Comparación", value=fecha_fin_fecha, key="cmp_fin_fecha")
                cmp_fin_hora = st.time_input("Hora Fin Comparación", value=fecha_fin_hora, key="cmp_fin_hora")
    b1, b2 = st.columns(2)
    with b1:
        submit = st.form_submit_button("Consultar")
    with b2:
        reset = st.form_submit_button("Reset filtros")

st.page_link("pages/operaciones_tiempo_real.py", label="⚡ Operaciones en tiempo real", icon="⚡")

if reset:
    for key in list(st.session_state.keys()):
        if key not in ("db_conn", "connection_name"):
            del st.session_state[key]
    st.experimental_rerun()

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
ok_count = len(df[df["pri_status"] == "O"])
pend_count = len(df[df["pri_status"] == "N"])
err_count = len(df[df["pri_status"] == "E"])

kpi_row = st.container()
with kpi_row:
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_kpi_card("Total", f"{total}", delta_total)
    with c2:
        render_kpi_card("OK", f"{ok_count}")
    with c3:
        render_kpi_card("Pendiente", f"{pend_count}")
    with c4:
        render_kpi_card("Error", f"{err_count}")

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
        if df.empty or "pri_status" not in df.columns:
            st.info("No data")
        else:
            status_counts = df["pri_status"].value_counts().reset_index()
            status_counts.columns = ["pri_status", "cantidad"]
            fig_status = px.bar(
                status_counts,
                x="pri_status",
                y="cantidad",
                labels={"pri_status": "Estado", "cantidad": "Transacciones"},
                title="Transacciones por estado",
                color="pri_status",
                color_discrete_sequence=PALETTE,
            )
            st.plotly_chart(fig_status, use_container_width=True)

# --- Errores por código ------------------------------------------------------
st.subheader("🧱 Errores por código")
col_top, col_toggle = st.columns([3, 1])
with col_top:
    top_n_codes = st.slider("Top N códigos", 5, 30, 10, key="top_err_codes")
with col_toggle:
    ver_completo = st.checkbox("Ver completo", value=False, key="ver_completo")

fig_err_codes = error_codes_bar(
    df,
    df_cmp if comparar else None,
    top_n=top_n_codes,
    full=ver_completo,
)
st.plotly_chart(fig_err_codes, use_container_width=True)

# --- Tabla de significado de errores ---
st.markdown("**Mapa de códigos ↔ mensaje normalizado**")
map_actual = _most_frequent_message_per_code(df)
if comparar:
    cur_counts = _prepare_error_code_counts(df)[["pri_error_code", "count"]].rename(columns={"count": "count_actual"})
    cmp_counts = _prepare_error_code_counts(df_cmp)[["pri_error_code", "count"]].rename(columns={"count": "count_cmp"})
    table = (
        map_actual
        .merge(cur_counts, on="pri_error_code", how="left")
        .merge(cmp_counts, on="pri_error_code", how="left")
    )
else:
    cur_counts = _prepare_error_code_counts(df)[["pri_error_code", "count"]].rename(columns={"count": "count_actual"})
    table = map_actual.merge(cur_counts, on="pri_error_code", how="left")

if table.empty:
    st.info("No data available")
else:
    table = table.fillna({"count_actual": 0, "count_cmp": 0}).sort_values("count_actual", ascending=False)
    st.dataframe(table, use_container_width=True)
    csv = table.to_csv(index=False).encode("utf-8")
    st.download_button("Descargar CSV", data=csv, file_name="errores.csv", mime="text/csv")

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

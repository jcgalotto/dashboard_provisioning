# pages/deteccion_anomalias.py
import datetime
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from data.query_builder import build_query
from services.data_service import get_transacciones
from ml.predict import score_anomalies
from utils.helpers import normalize_error_message

st.title("🧭 Detección de anomalías")

# -------------- Requisito: conexión activa --------------
if "db_conn" not in st.session_state:
    st.warning("🔌 No hay conexión activa")
    st.stop()

# -------------- Rangos rápidos + Fallback de filtros --------------
def _rango_rapido(now: datetime.datetime, n_horas: int):
    hoy0 = datetime.datetime.combine(now.date(), datetime.time(0, 0))
    return {
        "Últimas N horas": (now - datetime.timedelta(hours=n_horas), now),
        "Últimas 24 h": (now - datetime.timedelta(hours=24), now),
        "Últimos 7 días": (now - datetime.timedelta(days=7), now),
        "Hoy": (hoy0, now),
        "Ayer": (hoy0 - datetime.timedelta(days=1), hoy0 - datetime.timedelta(seconds=1)),
        "Personalizado": (None, None),
    }

def _get_filters_with_shortcuts():
    now = datetime.datetime.now()
    s = st.session_state

    st.subheader("🎯 Filtros de análisis")

    # Selector de rango y slider para "Últimas N horas"
    c1, c2 = st.columns([2, 1])
    with c2:
        n_horas = st.slider("N horas", min_value=1, max_value=72, value=24, step=1, key="anom_n_horas")
    with c1:
        rango_sel = st.selectbox("Rango rápido", ["Últimas N horas", "Últimas 24 h", "Últimos 7 días", "Hoy", "Ayer", "Personalizado"], index=0, key="anom_rango")

    rangos = _rango_rapido(now, n_horas)
    fi_def, ff_def = rangos[rango_sel]

    col1, col2 = st.columns(2)
    if rango_sel == "Personalizado" or fi_def is None:
        # Fallback si no venimos de Home: usar valores de sesión si existen
        def _def_dt(key, default_dt):
            v = s.get(key)
            if isinstance(v, datetime.datetime):
                return v.date(), v.time()
            return default_dt.date(), default_dt.time()

        d_ini, t_ini = _def_dt("fecha_ini", datetime.datetime(now.year, now.month, now.day, 0, 0))
        d_fin, t_fin = _def_dt("fecha_fin", now)

        with col1:
            fi_date = st.date_input("Fecha Inicio", value=d_ini, key="anomal_fi_date")
            fi_time = st.time_input("Hora Inicio", value=t_ini, key="anomal_fi_time")
        with col2:
            ff_date = st.date_input("Fecha Fin", value=d_fin, key="anomal_ff_date")
            ff_time = st.time_input("Hora Fin", value=t_fin, key="anomal_ff_time")

        fecha_ini = datetime.datetime.combine(fi_date, fi_time)
        fecha_fin = datetime.datetime.combine(ff_date, ff_time)
    else:
        fecha_ini, fecha_fin = fi_def, ff_def
        col1.info(f"Inicio: {fecha_ini:%Y-%m-%d %H:%M}")
        col2.info(f"Fin: {fecha_fin:%Y-%m-%d %H:%M}")

    ne_id = st.text_input("NE ID (opcional)", value=s.get("ne_id", ""), key="anomal_ne")
    ignorar_filtros = st.checkbox("Ignorar Servicios/Acciones (para probar)", value=True, key="anom_ignore_filters")

    # Persistir en sesión
    s["fecha_ini"], s["fecha_fin"], s["ne_id"] = fecha_ini, fecha_fin, ne_id

    selected_actions = None if ignorar_filtros else s.get("selected_actions")
    selected_services = None if ignorar_filtros else s.get("selected_services")

    buscar = st.button("🔎 Buscar / actualizar datos", use_container_width=True, key="anom_btn_search")
    return fecha_ini, fecha_fin, ne_id, selected_actions, selected_services, buscar

# --- Obtener filtros y disparar búsqueda ---
fecha_ini, fecha_fin, ne_id, selected_actions, selected_services, buscar = _get_filters_with_shortcuts()

# -------------- Construcción de query & carga con control de botón --------------
query = build_query(
    fecha_ini,
    fecha_fin,
    ne_id or None,
    selected_actions or None,
    selected_services or None,
)

# Cargar datos al apretar Buscar o en el primer render
if buscar or "anom_first" not in st.session_state:
    st.session_state["anom_first"] = True
    df = get_transacciones(st.session_state["db_conn"], query)
    st.session_state["anom_df"] = df
else:
    df = st.session_state.get("anom_df", pd.DataFrame())

# -------------- Diagnóstico (SQL y conteos) --------------
with st.expander("🔧 Ver SQL y conteos"):
    st.code(query, language="sql")
    st.write(f"Total filas: **{len(df)}**")
    if not df.empty and "pri_status" in df.columns:
        st.write("Distribución por pri_status:")
        st.dataframe(
            df["pri_status"].value_counts().rename_axis("pri_status").reset_index(name="count"),
            use_container_width=True
        )

# -------------- Sin datos → hints y stop --------------
if df is None or df.empty:
    st.warning("Sin datos para el rango/criterios seleccionados.")
    st.info(
        "- Probá **Últimas N horas** (ajustando el slider) o **Últimos 7 días**.\n"
        "- Activá **Ignorar Servicios/Acciones** para descartar filtros.\n"
        "- Verificá que la columna temporal usada por la SQL coincida con tu ventana."
    )
    st.stop()

# -------------- Scoring de anomalías --------------
try:
    scored = score_anomalies(df)
except FileNotFoundError:
    st.error("No hay modelo entrenado en models/anomaly_isoforest.pkl. Entrená el modelo primero.")
    st.stop()
except Exception as e:
    st.error(f"Error al puntuar anomalías: {e}")
    st.stop()

# Preparar columnas de contexto
scored = scored.copy()
scored["pri_error_code_str"] = (
    scored.get("pri_error_code", "").astype(str).str.replace(r"\.0$", "", regex=True)
)
scored["pri_message_error_norm"] = (
    scored.get("pri_message_error", "")
    .astype(str)
    .fillna("")
    .apply(normalize_error_message)
)

# -------------- Controles UI de visualización --------------
st.subheader("Resultados")
col_a, col_b, col_c = st.columns(3)
with col_a:
    top_k = st.number_input("Top K más anómalos", min_value=5, max_value=500, value=50, step=5, key="anom_topk")
with col_b:
    threshold = st.slider("Umbral score (más negativo = más anómalo)", min_value=-0.5, max_value=0.5, value=-0.05, step=0.01, key="anom_th")
with col_c:
    solo_anomalos = st.checkbox("Mostrar sólo anomalías (is_anomaly = 1)", value=True, key="anom_only")

scored_sorted = scored.sort_values("anomaly_score", ascending=True)
view = scored_sorted[scored_sorted["is_anomaly"] == 1] if solo_anomalos else scored_sorted
view = view[view["anomaly_score"] <= threshold].head(top_k)

# -------------- Gráfico: barras por rareza (−score) --------------
fig = go.Figure()
fig.add_trace(go.Bar(
    x=-view["anomaly_score"],  # invertimos para que barra alta = más anómalo
    y=view["pri_error_code_str"],
    orientation="h",
    hovertext=[
        f"Score: {s:.4f}<br>Código: {c}<br>Mensaje: {m}"
        for s, c, m in zip(
            view["anomaly_score"], view["pri_error_code_str"], view["pri_message_error_norm"]
        )
    ],
    hoverinfo="text+x"
))
fig.update_layout(
    height=520,
    margin=dict(l=10, r=10, t=40, b=10),
    xaxis_title="Rareza (−score)",
    yaxis_title="Código de error",
    yaxis=dict(type="category"),
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)'
)
st.plotly_chart(fig, use_container_width=True)

# -------------- Tabla + descarga --------------
st.subheader("Tabla de anomalías seleccionadas")
cols_pref = [
    "anomaly_score", "is_anomaly", "pri_error_code_str", "pri_message_error_norm",
    "pri_status", "pri_ne_service", "pri_action", "pri_action_date"
]
cols_show = [c for c in cols_pref if c in view.columns]
st.dataframe(view[cols_show].reset_index(drop=True), use_container_width=True)

csv = view[cols_show].to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Descargar anomalías (CSV)", data=csv, file_name="anomalias_topK.csv", mime="text/csv")

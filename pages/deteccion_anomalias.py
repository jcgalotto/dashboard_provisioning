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

# Requisito: conexión activa
if "db_conn" not in st.session_state:
    st.warning("🔌 No hay conexión activa")
    st.stop()

# --- Fallback de filtros: leer de session_state o pedirlos aquí ---
def _get_filters():
    now = datetime.datetime.now()

    # Intentar leer desde sesión (si venimos de la home)
    fecha_ini = st.session_state.get("fecha_ini", None)
    fecha_fin = st.session_state.get("fecha_fin", None)
    ne_id = st.session_state.get("ne_id", "")
    selected_actions = st.session_state.get("selected_actions", None)
    selected_services = st.session_state.get("selected_services", None)

    # Si faltan fechas válidas, pedirlas localmente
    if not isinstance(fecha_ini, datetime.datetime) or not isinstance(fecha_fin, datetime.datetime):
        st.info("Usá estos filtros si entraste directo a esta página (se guardan en la sesión).")
        col1, col2 = st.columns(2)
        with col1:
            fi_date = st.date_input("Fecha Inicio", value=now.date(), key="anomal_fi_date")
            fi_time = st.time_input("Hora Inicio", value=datetime.time(0, 0), key="anomal_fi_time")
        with col2:
            ff_date = st.date_input("Fecha Fin", value=now.date(), key="anomal_ff_date")
            ff_time = st.time_input("Hora Fin", value=now.time(), key="anomal_ff_time")

        fecha_ini = datetime.datetime.combine(fi_date, fi_time)
        fecha_fin = datetime.datetime.combine(ff_date, ff_time)

        # NE opcional si no venía seteado
        ne_id = st.text_input("NE ID (opcional)", value=ne_id, key="anomal_ne")

        # Persistir en sesión para mantener consistencia
        st.session_state["fecha_ini"] = fecha_ini
        st.session_state["fecha_fin"] = fecha_fin
        st.session_state["ne_id"] = ne_id

    return fecha_ini, fecha_fin, ne_id, selected_actions, selected_services

fecha_ini, fecha_fin, ne_id, selected_actions, selected_services = _get_filters()

# --- Construcción de query y carga de datos ---
query = build_query(
    fecha_ini,
    fecha_fin,
    ne_id or None,
    selected_actions or None,
    selected_services or None,
)

df = get_transacciones(st.session_state["db_conn"], query)

if df is None or df.empty:
    st.info("Sin datos para el rango/criterios seleccionados.")
    st.stop()

# --- Scoring de anomalías (IsolationForest) ---
try:
    scored = score_anomalies(df)
except FileNotFoundError:
    st.error("No hay modelo entrenado (models/anomaly_isoforest.pkl). Entrená el modelo primero.")
    st.stop()

# Preparar columnas de contexto para visualizar
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

# --- Controles UI ---
st.subheader("Resultados")
col_a, col_b, col_c = st.columns(3)
with col_a:
    top_k = st.number_input("Top K más anómalos", min_value=5, max_value=500, value=50, step=5)
with col_b:
    threshold = st.slider("Umbral score (más negativo = más anómalo)", min_value=-0.5, max_value=0.5, value=-0.05, step=0.01)
with col_c:
    solo_anomalos = st.checkbox("Mostrar sólo anomalías (is_anomaly=1)", value=True)

# Ordenar por rareza (score más negativo primero)
scored_sorted = scored.sort_values("anomaly_score", ascending=True)

if solo_anomalos:
    view = scored_sorted[scored_sorted["is_anomaly"] == 1]
else:
    view = scored_sorted

# Umbral + Top K
view = view[view["anomaly_score"] <= threshold].head(top_k)

# --- Gráfico: barras por rareza (−score = más raro) ---
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

# --- Tabla + descarga ---
st.subheader("Tabla de anomalías seleccionadas")
cols_pref = [
    "anomaly_score", "is_anomaly", "pri_error_code_str", "pri_message_error_norm",
    "pri_status", "pri_ne_service", "pri_action", "pri_action_date"
]
cols_show = [c for c in cols_pref if c in view.columns]
st.dataframe(view[cols_show].reset_index(drop=True), use_container_width=True)

csv = view[cols_show].to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Descargar anomalías (CSV)", csv, "anomalias_topK.csv", "text/csv")

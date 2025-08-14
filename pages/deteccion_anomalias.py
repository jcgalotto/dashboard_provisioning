import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from data.query_builder import build_query
from services.data_service import get_transacciones
from ml.predict import score_anomalies
from utils.helpers import normalize_error_message

st.set_page_config(page_title="Detección de anomalías")
st.markdown(
    """
    <style>
    div[data-testid='stSidebarNav'] { display: none; }
    [data-testid='stHeader'] { display: none; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🧭 Detección de anomalías")

# Requisitos de conexión
if "db_conn" not in st.session_state:
    st.warning("🔌 No hay conexión activa")
    st.stop()

# Reusa fechas/hora/NE/acciones/servicios desde st.session_state si ya se cargan en app.py
fecha_ini = st.session_state.get("fecha_ini")
fecha_fin = st.session_state.get("fecha_fin")
ne_id = st.session_state.get("ne_id")
selected_actions = st.session_state.get("selected_actions")
selected_services = st.session_state.get("selected_services")

# Si no existen, podés agregar inputs rápidos acá o dejar que vengan seteados desde la home
query = build_query(fecha_ini, fecha_fin, ne_id, selected_actions, selected_services)
df = get_transacciones(st.session_state["db_conn"], query)

if df.empty:
    st.info("Sin datos para el rango/criterios seleccionados.")
    st.stop()

# Scoring
try:
    scored = score_anomalies(df)
except FileNotFoundError:
    st.error("No hay modelo entrenado (models/anomaly_isoforest.pkl). Entrená el modelo primero.")
    st.stop()

# Controles UI
st.subheader("Resultados")
col_a, col_b, col_c = st.columns(3)
with col_a:
    top_k = st.number_input("Top K más anómalos", min_value=5, max_value=500, value=50, step=5)
with col_b:
    threshold = st.slider("Umbral score (más negativo = más anómalo)", min_value=-0.5, max_value=0.5, value=-0.05, step=0.01)
with col_c:
    solo_anomalos = st.checkbox("Mostrar sólo anomalías (is_anomaly=1)", value=True)

# Prepara columnas de contexto
scored_sorted = scored.sort_values("anomaly_score", ascending=True).copy()
scored_sorted["pri_error_code_str"] = (
    scored_sorted.get("pri_error_code", "").astype(str).str.replace(r"\.0$", "", regex=True)
)
scored_sorted["pri_message_error_norm"] = scored_sorted.get("pri_message_error", "").astype(str).fillna("").apply(normalize_error_message)

# Filtra
if solo_anomalos:
    view = scored_sorted[scored_sorted["is_anomaly"] == 1]
else:
    view = scored_sorted
view = view[view["anomaly_score"] <= threshold].head(top_k)

# Gráfico: barras por rareza (−score)
fig = go.Figure()
fig.add_trace(go.Bar(
    x=-view["anomaly_score"],  # invertimos para que barra alta = más anómalo
    y=view["pri_error_code_str"],
    orientation="h",
    hovertext=[f"Score: {s:.4f}<br>Código: {c}<br>Mensaje: {m}" for s, c, m in zip(view["anomaly_score"], view["pri_error_code_str"], view["pri_message_error_norm"])],
    hoverinfo="text+x"
))
fig.update_layout(
    height=520, margin=dict(l=10,r=10,t=40,b=10),
    xaxis_title="Rareza (−score)", yaxis_title="Código de error",
    yaxis=dict(type="category"),
    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)'
)
st.plotly_chart(fig, use_container_width=True)

# Tabla + descarga
st.subheader("Tabla de anomalías seleccionadas")
cols_show = [
    "anomaly_score", "is_anomaly", "pri_error_code_str", "pri_message_error_norm",
    "pri_status", "pri_ne_service", "pri_action", "pri_action_date"
]
exists = [c for c in cols_show if c in view.columns]
st.dataframe(view[exists].reset_index(drop=True), use_container_width=True)

csv = view[exists].to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Descargar anomalías (CSV)", csv, "anomalias_topK.csv", "text/csv")

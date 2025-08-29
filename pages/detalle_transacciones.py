import streamlit as st
import pandas as pd
from utils.helpers import normalize_error_message, generar_insert

try:
    from st_aggrid import AgGrid
    HAS_AGGRID = True
except ImportError:
    HAS_AGGRID = False

st.set_page_config(page_title="Detalle de transacciones")
st.markdown(
    """
    <style>
    div[data-testid='stSidebarNav'] { display: none; }
    [data-testid='stHeader'] { display: none; }
    </style>
    """,
    unsafe_allow_html=True,
)
st.title("📄 Detalle de transacciones")

df = st.session_state.get("transacciones_df")

if df is None:
    st.warning("No hay datos de transacciones en la sesión")
else:
    estados = ["Todos"] + df["pri_status"].dropna().unique().tolist()
    estado = st.selectbox("Filtrar por estado", estados)

    df_filtrado = (
        df if estado == "Todos" else df[df["pri_status"] == estado]
    ).copy()

    if estado == "E":
        errores = ["Todos"] + df_filtrado["pri_error_code"].dropna().unique().tolist()
        error = st.selectbox("Tipo de error", errores)
        if error != "Todos":
            df_filtrado = df_filtrado[df_filtrado["pri_error_code"] == error].copy()

        df_filtrado["pri_message_error"] = df_filtrado["pri_message_error"].apply(
            normalize_error_message
        )
        mensajes = ["Todos"] + df_filtrado["pri_message_error"].dropna().unique().tolist()
        mensaje = st.selectbox("Descripción del error", mensajes)
        if mensaje != "Todos":
            df_filtrado = df_filtrado[df_filtrado["pri_message_error"] == mensaje]

    if HAS_AGGRID:
        AgGrid(df_filtrado)
    else:
        st.dataframe(df_filtrado)

    if not df_filtrado.empty:
        inserts = [generar_insert(fila.to_dict()) for _, fila in df_filtrado.iterrows()]

        sql_contenido = "\n".join(inserts)

        st.download_button(
            "Generar insert SQL",
            data=sql_contenido,
            file_name="transacciones_insert.sql",
            mime="application/sql",
        )

if st.button("Volver"):
    st.switch_page("app.py")

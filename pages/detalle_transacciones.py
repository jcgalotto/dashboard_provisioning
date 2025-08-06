import streamlit as st

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

    df_filtrado = df if estado == "Todos" else df[df["pri_status"] == estado]

    if estado == "E":
        errores = ["Todos"] + df_filtrado["pri_error_code"].dropna().unique().tolist()
        error = st.selectbox("Tipo de error", errores)
        if error != "Todos":
            df_filtrado = df_filtrado[df_filtrado["pri_error_code"] == error]

    if HAS_AGGRID:
        AgGrid(df_filtrado)
    else:
        st.dataframe(df_filtrado)

if st.button("Volver"):
    st.switch_page("app.py")

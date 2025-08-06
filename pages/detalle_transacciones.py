import streamlit as st
import pandas as pd

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

    if not df_filtrado.empty:
        columnas = ", ".join(df_filtrado.columns)

        inserts = []
        for _, fila in df_filtrado.iterrows():
            valores = []
            for valor in fila:
                if pd.isna(valor):
                    valores.append("NULL")
                elif isinstance(valor, str):
                    valores.append("'" + valor.replace("'", "''") + "'")
                else:
                    valores.append(str(valor))
            inserts.append(
                f"INSERT INTO swp_provisioning_interfaces ({columnas}) VALUES ({', '.join(valores)});"
            )

        sql_contenido = "\n".join(inserts)

        st.download_button(
            "Generar insert SQL",
            data=sql_contenido,
            file_name="transacciones_insert.sql",
            mime="application/sql",
        )

if st.button("Volver"):
    st.switch_page("app.py")

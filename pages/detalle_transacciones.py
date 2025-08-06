import streamlit as st
import pandas as pd
import datetime

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
            for col, valor in fila.items():
                if col.lower() == "pri_id":
                    valores.append("(SELECT MAX(pri_id) + 1 FROM swp_provisioning_interfaces)")
                elif pd.isna(valor):
                    valores.append("NULL")
                elif (
                    "date" in col.lower()
                    or pd.api.types.is_datetime64_any_dtype(df_filtrado[col])
                    or isinstance(valor, (pd.Timestamp, datetime.datetime, datetime.date))
                ):
                    if isinstance(valor, str) and valor.upper() == "SYSDATE":
                        valores.append("TO_DATE(SYSDATE, 'DD-MM-YYYY HH24:MI:SS')")
                    else:
                        fecha = pd.to_datetime(valor)
                        valores.append(
                            f"TO_DATE('{fecha.strftime('%d-%m-%Y %H:%M:%S')}', 'DD-MM-YYYY HH24:MI:SS')"
                        )
                elif isinstance(valor, str):
                    valores.append("'" + valor.replace("'", "''") + "'")
                else:
                    valores.append(str(valor))
            inserts.append(
                f"INSERT INTO swp_provisioning_interfaces ({columnas}) VALUES ({', '.join(valores)});",
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

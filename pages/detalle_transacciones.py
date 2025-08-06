import streamlit as st

try:
    from st_aggrid import AgGrid
    HAS_AGGRID = True
except ImportError:
    HAS_AGGRID = False

st.set_page_config(page_title="Detalle de transacciones")
st.title("📄 Detalle de transacciones")

df = st.session_state.get("transacciones_df")

if df is None:
    st.warning("No hay datos de transacciones en la sesión")
else:
    if HAS_AGGRID:
        AgGrid(df)
    else:
        st.dataframe(df)

if st.button("Volver"):
    st.switch_page("app")

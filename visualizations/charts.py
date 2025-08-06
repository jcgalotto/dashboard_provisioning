import streamlit as st
import plotly.express as px


def kpi_cards(df):
    total = len(df)
    pendiente = len(df[df["pri_status"].isin(["K", "T", "PENDING"])])
    ok = len(df[df["pri_status"] == "O"])
    error = len(df[df["pri_status"] == "E"])

    if total == 0:
        st.warning("No data available")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total", total)
    col2.metric("Pendiente", pendiente)
    col3.metric("OK", ok)
    col4.metric("Error", error)


def status_pie_chart(df):
    if df.empty:
        st.warning("No data available")
        return px.Figure()
    counts = df["pri_status"].value_counts().reset_index()
    counts.columns = ["Status", "Cantidad"]
    return px.pie(counts, names="Status", values="Cantidad", title="Distribución de Status")


def error_bar_chart(df):
    if df.empty:
        st.warning("No data available")
        return px.Figure()
    errores = df[df["pri_status"] == "E"]
    conteo = errores["pri_error_code"].value_counts().reset_index()
    conteo.columns = ["Código Error", "Cantidad"]
    return px.bar(conteo, x="Código Error", y="Cantidad", title="Errores por Código", color="Cantidad")


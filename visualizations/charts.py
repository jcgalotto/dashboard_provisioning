import streamlit as st
import plotly.express as px


def kpi_cards(df):
    total = len(df)
    ok = len(df[df["pri_status"] == "O"])
    error = len(df[df["pri_status"] == "E"])
    perc_ok = (ok / total) * 100 if total > 0 else 0
    perc_err = (error / total) * 100 if total > 0 else 0

    if total == 0:
        st.warning("No data available")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total", total)
    col2.metric("% OK", f"{perc_ok:.2f}%")
    col3.metric("% Error", f"{perc_err:.2f}%")


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


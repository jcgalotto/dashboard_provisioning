import streamlit as st
import plotly.express as px


def kpi_cards(df):
    total = len(df)
    pendiente = len(df[df["pri_status"].isin(["K", "T", "PENDING"])])
    ok = len(df[df["pri_status"] == "O"])
    error = len(df[df["pri_status"] == "E"])

    if total == 0:
        st.warning("No data available")

    if total > 0:
        pendiente_pct = pendiente / total
        ok_pct = ok / total
        error_pct = error / total
        total_pct = 1
    else:
        pendiente_pct = 0
        ok_pct = 0
        error_pct = 0
        total_pct = 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total", total, f"{total_pct:.2%}")
    col2.metric("Pendiente", pendiente, f"{pendiente_pct:.2%}")
    col3.metric("OK", ok, f"{ok_pct:.2%}")
    col4.metric("Error", error, f"{error_pct:.2%}")


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


def error_detail_bar_chart(df):
    if df.empty:
        st.warning("No data available")
        return px.Figure()
    errores = df[df["pri_status"] == "E"]
    conteo = (
        errores.groupby(["pri_error_code", "pri_message_error"])
        .size()
        .reset_index(name="Cantidad")
    )
    conteo.columns = ["Código Error", "Descripción", "Cantidad"]
    return px.bar(
        conteo,
        x="Código Error",
        y="Cantidad",
        color="Descripción",
        title="Errores por Código y Descripción",
    )


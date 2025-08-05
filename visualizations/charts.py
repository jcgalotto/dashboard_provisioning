
import streamlit as st
import plotly.express as px

def kpi_cards(df):
    total = len(df)
    ok = len(df[df["pri_status"] == "O"])
    error = len(df[df["pri_status"] == "E"])
    perc_ok = (ok / total) * 100 if total > 0 else 0
    perc_err = (error / total) * 100 if total > 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.markdown(f"<div style='padding:20px; background:#e8f5e9; border-radius:10px'><h3>Total</h3><h1>{total}</h1></div>", unsafe_allow_html=True)
    col2.markdown(f"<div style='padding:20px; background:#e3f2fd; border-radius:10px'><h3>% OK</h3><h1>{perc_ok:.2f}%</h1></div>", unsafe_allow_html=True)
    col3.markdown(f"<div style='padding:20px; background:#ffebee; border-radius:10px'><h3>% Error</h3><h1>{perc_err:.2f}%</h1></div>", unsafe_allow_html=True)

def status_pie_chart(df):
    counts = df['pri_status'].value_counts().reset_index()
    counts.columns = ['Status', 'Cantidad']
    return px.pie(counts, names='Status', values='Cantidad', title="Distribución de Status")

def error_bar_chart(df):
    errores = df[df["pri_status"] == "E"]
    conteo = errores["pri_error_code"].value_counts().reset_index()
    conteo.columns = ["Código Error", "Cantidad"]
    return px.bar(conteo, x="Código Error", y="Cantidad", title="Errores por Código", color="Cantidad")

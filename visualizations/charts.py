import streamlit as st
import plotly.express as px
import pandas as pd

# Explicitly export the public chart helpers so ``from visualizations.charts``
# always exposes the expected functions even in older Python environments.
__all__ = [
    "kpi_cards",
    "error_comparison_bar_chart",
    "realtime_operations_chart",
]


def kpi_cards(df: pd.DataFrame) -> None:
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


def error_comparison_bar_chart(
    resumen_actual: pd.DataFrame, resumen_cmp: pd.DataFrame
) -> px.bar:
    if resumen_actual.empty and resumen_cmp.empty:
        st.warning("No data available")
        return px.Figure()
    resumen_total = (
        resumen_actual.merge(
            resumen_cmp,
            on=["pri_error_code", "pri_message_error"],
            how="outer",
            suffixes=("_actual", "_cmp"),
        ).fillna(0)
    )
    resumen_total["diferencia"] = (
        resumen_total["cantidad_actual"] - resumen_total["cantidad_cmp"]
    )
    return px.bar(
        resumen_total,
        x="pri_error_code",
        y="diferencia",
        color="pri_message_error",
        labels={
            "pri_error_code": "Código Error",
            "diferencia": "Diferencia",
            "pri_message_error": "Descripción",
        },
        title="Diferencia de errores entre periodos",
    )


def realtime_operations_chart(df: pd.DataFrame) -> px.line:
    """Generate a real-time operations line chart.

    The data frame is aggregated per minute using the ``pri_action_date``
    column. When no data is provided a blank :class:`plotly.graph_objs.Figure`
    is returned so importing the function never fails.
    """

    if df.empty or "pri_action_date" not in df.columns:
        st.warning("No data available")
        return px.Figure()

    df_ts = (
        df.assign(pri_action_date=pd.to_datetime(df["pri_action_date"]))
        .groupby(pd.Grouper(key="pri_action_date", freq="1min"))
        .size()
        .reset_index(name="cantidad")
    )

    return px.line(
        df_ts,
        x="pri_action_date",
        y="cantidad",
        labels={"pri_action_date": "Hora", "cantidad": "Operaciones"},
        title="Operaciones en tiempo real",
    )


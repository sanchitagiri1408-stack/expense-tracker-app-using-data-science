"""Streamlit dashboard for the Expense Tracker App.

Start it from the project root with:

    streamlit run app.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from main import run_pipeline
from src.analyzer import ExpenseAnalyzer
from src.config import CLEANED_DATA_PATH, CURRENCY, END_DATE, START_DATE, format_currency
from src.data_cleaner import DataCleaner
from src.visualizer import ExpenseVisualizer


st.set_page_config(
    page_title="Expense Tracker Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data(show_spinner=False)
def load_default_data() -> pd.DataFrame:
    """Load the cleaned sample, generating it when a fresh clone has no data."""

    if not Path(CLEANED_DATA_PATH).exists():
        run_pipeline(generate_charts=False)
    data = pd.read_csv(CLEANED_DATA_PATH)
    data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
    return data


@st.cache_data(show_spinner=False)
def clean_uploaded_data(file_bytes: bytes) -> pd.DataFrame:
    """Clean an uploaded CSV using the same rules as the CLI pipeline."""

    from io import BytesIO

    raw = pd.read_csv(BytesIO(file_bytes))
    cleaned = DataCleaner(data=raw).clean_data()
    return cleaned


def select_data() -> tuple[pd.DataFrame, str]:
    """Return selected data and a short source label."""

    uploaded = st.sidebar.file_uploader(
        "Optional: upload an expense CSV",
        type=["csv"],
        help="Required columns: Date, Category, Amount, Payment_Method.",
    )
    if uploaded is not None:
        try:
            return clean_uploaded_data(uploaded.getvalue()), "Uploaded CSV"
        except Exception as error:  # pragma: no cover - exercised interactively
            st.sidebar.error(f"Could not read this CSV: {error}")
            st.stop()
    return load_default_data(), "Reproducible synthetic sample"


def main() -> None:
    """Render the dashboard."""

    st.title("💰 Expense Tracker App using Data Science")
    st.caption(
        "A beginner-friendly analytics portfolio project. The default dataset is synthetic and the dashboard is not financial advice."
    )

    data, source = select_data()
    if data.empty:
        st.warning("No expense records are available. Generate or upload a CSV to continue.")
        st.stop()

    st.sidebar.header("Filters")
    min_date = data["Date"].min().date()
    max_date = data["Date"].max().date()
    selected_range = st.sidebar.date_input(
        "Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
    if isinstance(selected_range, tuple) and len(selected_range) == 2:
        start_date, end_date = selected_range
    else:
        start_date = end_date = selected_range

    selected_categories = st.sidebar.multiselect(
        "Categories",
        options=sorted(data["Category"].dropna().unique()),
        default=sorted(data["Category"].dropna().unique()),
    )
    selected_methods = st.sidebar.multiselect(
        "Payment methods",
        options=sorted(data["Payment_Method"].dropna().unique()),
        default=sorted(data["Payment_Method"].dropna().unique()),
    )

    filtered = data[
        data["Date"].between(pd.Timestamp(start_date), pd.Timestamp(end_date))
        & data["Category"].isin(selected_categories)
        & data["Payment_Method"].isin(selected_methods)
    ].copy()

    st.info(f"Data source: **{source}** · Showing {len(filtered):,} of {len(data):,} transactions")
    if filtered.empty:
        st.warning("No rows match the selected filters. Broaden the date, category, or payment selections.")
        st.stop()

    analyzer = ExpenseAnalyzer(data=filtered, currency=CURRENCY)
    analyzer.analyze_all()
    visualizer = ExpenseVisualizer(filtered, currency=CURRENCY)
    kpis = analyzer.get_statistics()

    columns = st.columns(5)
    cards = [
        ("Total spending", format_currency(kpis["total_expenses"])),
        ("Average transaction", format_currency(kpis["average_transaction"])),
        ("Average per day", format_currency(kpis["average_daily_spending"])),
        ("Highest transaction", format_currency(kpis["max_transaction"])),
        ("Transactions", f"{kpis['transaction_count']:,}"),
    ]
    for column, (label, value) in zip(columns, cards):
        column.metric(label, value)

    st.subheader("Spending overview")
    chart_left, chart_right = st.columns(2)
    with chart_left:
        st.plotly_chart(visualizer.create_interactive_category_pie(), use_container_width=True)
    with chart_right:
        st.plotly_chart(visualizer.create_interactive_monthly_trend(), use_container_width=True)

    st.plotly_chart(visualizer.create_interactive_category_bar(), use_container_width=True)

    table_left, table_right = st.columns(2)
    with table_left:
        st.subheader("Category analysis")
        st.dataframe(analyzer.tables["category_summary"], use_container_width=True, hide_index=True)
    with table_right:
        st.subheader("Monthly trend")
        st.dataframe(analyzer.tables["monthly_summary"], use_container_width=True, hide_index=True)

    st.subheader("Generated insights")
    for message in analyzer.get_insights():
        st.markdown(f"- {message}")

    anomaly_count = int(kpis.get("anomalies", {}).get("flagged_count", 0))
    if anomaly_count:
        st.subheader("Transactions for review")
        st.warning(
            f"{anomaly_count} transaction(s) are unusual relative to their category. This is a review signal, not a fraud conclusion."
        )
        st.dataframe(analyzer.tables["anomaly_records"].head(20), use_container_width=True, hide_index=True)

    st.download_button(
        "Download filtered CSV",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="filtered_expenses.csv",
        mime="text/csv",
    )

    with st.expander("About this project"):
        st.markdown(
            "This dashboard demonstrates data input, cleaning, feature engineering, descriptive analysis, visualization, and decision-oriented insight generation. The default records are reproducible synthetic data generated with a fixed seed."
        )


if __name__ == "__main__":
    main()

"""Behavior-focused tests for the Expense Tracker pipeline."""

from __future__ import annotations

import pandas as pd

from main import run_pipeline
from src.analyzer import ExpenseAnalyzer
from src.data_cleaner import DataCleaner
from src.data_generator import DataGenerator
from src.visualizer import ExpenseVisualizer


def test_generator_is_reproducible_and_contains_expected_schema() -> None:
    first = DataGenerator(num_records=80, seed=7, start_date="2024-01-01", end_date="2024-03-31").generate_data()
    second = DataGenerator(num_records=80, seed=7, start_date="2024-01-01", end_date="2024-03-31").generate_data()

    pd.testing.assert_frame_equal(first, second)
    assert len(first) == 80
    assert set(["Expense_ID", "Date", "Category", "Amount", "Payment_Method"]).issubset(first.columns)
    assert first["Amount"].gt(0).all()
    assert first["Category"].nunique() >= 3
    assert first["Date"].min() >= pd.Timestamp("2024-01-01")
    assert first["Date"].max() <= pd.Timestamp("2024-03-31")


def test_cleaner_removes_invalid_rows_and_adds_features() -> None:
    raw = pd.DataFrame(
        [
            {
                "Expense_ID": "EXP-1",
                "Date": "2024-01-02",
                "Category": "food",
                "Amount": "100",
                "Payment_Method": "upi",
                "Description": " lunch ",
                "Recurring": "false",
            },
            {
                "Expense_ID": "EXP-1",
                "Date": "2024-01-02",
                "Category": "food",
                "Amount": "100",
                "Payment_Method": "upi",
                "Description": "duplicate",
                "Recurring": "false",
            },
            {
                "Expense_ID": "EXP-2",
                "Date": "2024-01-03",
                "Category": "travel",
                "Amount": -20,
                "Payment_Method": "cash",
                "Description": "invalid amount",
                "Recurring": False,
            },
            {
                "Expense_ID": "EXP-3",
                "Date": "2025-01-03",
                "Category": "rent",
                "Amount": 19000,
                "Payment_Method": "bank transfer",
                "Description": "future row",
                "Recurring": True,
            },
        ]
    )

    cleaner = DataCleaner(data=raw, as_of="2024-12-31")
    cleaned = cleaner.clean_data()

    assert len(cleaned) == 1
    assert cleaned.loc[0, "Category"] == "Food & Dining"
    assert cleaned.loc[0, "Payment_Method"] == "Mobile Payment"
    for column in ["YearMonth", "DayOfWeek", "IsWeekend", "SpendingLevel", "CategoryRatio", "CumulativeMonthlySpend"]:
        assert column in cleaned.columns
    assert cleaned["Amount"].gt(0).all()
    assert cleaner.get_cleaning_report()["duplicates_removed"] == 1
    assert cleaner.get_cleaning_report()["invalid_amounts_removed"] == 1
    assert cleaner.get_cleaning_report()["future_dates_removed"] == 1


def test_analyzer_returns_kpis_and_actionable_tables() -> None:
    raw = DataGenerator(num_records=120, seed=12).generate_data()
    cleaned = DataCleaner(data=raw, as_of="2024-12-31").clean_data()
    analyzer = ExpenseAnalyzer(cleaned)
    tables = analyzer.analyze_all()

    assert analyzer.get_statistics()["transaction_count"] == len(cleaned)
    assert analyzer.get_statistics()["total_expenses"] == round(float(cleaned["Amount"].sum()), 2)
    assert {"category_summary", "monthly_summary", "payment_summary", "day_of_week_summary"}.issubset(tables)
    assert len(analyzer.get_insights()) >= 4
    assert "Is_Overspending" in analyzer.tables["monthly_overspending"].columns


def test_end_to_end_pipeline_writes_reports_and_charts(tmp_path) -> None:
    result = run_pipeline(
        num_records=90,
        seed=3,
        start_date="2024-01-01",
        end_date="2024-03-31",
        data_dir=tmp_path / "data",
        output_dir=tmp_path / "outputs",
        generate_charts=False,
    )

    assert result["raw_path"].exists()
    assert result["cleaned_path"].exists()
    assert (result["reports_dir"] / "kpis.json").exists()
    assert (result["reports_dir"] / "insights.txt").exists()
    assert result["cleaned_rows"] == 90


def test_visualizer_creates_static_evidence(tmp_path) -> None:
    raw = DataGenerator(num_records=100, seed=9).generate_data()
    cleaned = DataCleaner(data=raw, as_of="2024-12-31").clean_data()
    paths = ExpenseVisualizer(cleaned, output_dir=tmp_path).visualize_all()

    assert len(paths) >= 6
    assert all(path.exists() and path.stat().st_size > 0 for path in paths.values())

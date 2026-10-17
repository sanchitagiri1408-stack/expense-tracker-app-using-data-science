"""Data-quality and feature-engineering pipeline for expense records."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.config import (
    CLEANED_DATA_PATH,
    EXPENSE_CATEGORIES,
    OUTLIER_THRESHOLD,
    PAYMENT_METHODS,
    RAW_DATA_PATH,
)


REQUIRED_COLUMNS = {
    "Date",
    "Category",
    "Amount",
    "Payment_Method",
}


class DataCleaner:
    """Clean, validate, enrich, and report on an expense DataFrame."""

    def __init__(
        self,
        filepath: Path | str | None = RAW_DATA_PATH,
        data: pd.DataFrame | None = None,
        as_of: pd.Timestamp | str | None = None,
    ) -> None:
        if data is not None:
            self.raw_data = data.copy()
        elif filepath is not None:
            self.raw_data = pd.read_csv(filepath)
        else:
            self.raw_data = pd.DataFrame()
        self.as_of = pd.Timestamp(as_of).normalize() if as_of is not None else pd.Timestamp.now().normalize()
        self.cleaned_data: pd.DataFrame | None = None
        self.cleaning_report: dict[str, Any] = {}

    def load_data(self, filepath: Path | str = RAW_DATA_PATH) -> pd.DataFrame:
        """Load a raw CSV and return it."""

        self.raw_data = pd.read_csv(filepath)
        return self.raw_data.copy()

    @staticmethod
    def _normalise_text(value: object, default: str) -> str:
        """Trim a value and return a readable default when it is blank."""

        if pd.isna(value) or str(value).strip() == "":
            return default
        return str(value).strip()

    @staticmethod
    def _normalise_bool(series: pd.Series) -> pd.Series:
        """Convert common CSV boolean representations safely."""

        truthy = {"true", "1", "yes", "y", "t"}
        return series.map(lambda value: str(value).strip().lower() in truthy).astype(bool)

    def _ensure_columns(self) -> None:
        """Add optional columns and fail clearly when required fields are absent."""

        missing_required = REQUIRED_COLUMNS.difference(self.raw_data.columns)
        if missing_required:
            raise ValueError(
                "Input data is missing required columns: "
                + ", ".join(sorted(missing_required))
            )

        defaults = {
            "Expense_ID": None,
            "Description": "Uncategorised expense",
            "Tags": "misc",
            "Notes": "",
            "Recurring": False,
        }
        for column, default in defaults.items():
            if column not in self.raw_data.columns:
                self.raw_data[column] = default

    def check_missing_values(self) -> dict[str, int]:
        """Return the pre-cleaning missing-value count by column."""

        missing = self.raw_data.isna().sum()
        report = {str(column): int(count) for column, count in missing.items() if count}
        self.cleaning_report["missing_values_before"] = report
        self.cleaning_report["missing_values"] = int(sum(report.values()))
        return report

    def remove_duplicates(self) -> int:
        """Remove exact duplicate rows and repeated non-empty expense IDs."""

        before = len(self.raw_data)
        self.raw_data = self.raw_data.drop_duplicates(keep="first")
        exact_removed = before - len(self.raw_data)

        if "Expense_ID" in self.raw_data.columns:
            id_values = self.raw_data["Expense_ID"].astype("string").str.strip()
            valid_ids = id_values.notna() & id_values.ne("") & id_values.ne("<NA>")
            duplicate_ids = valid_ids & id_values.duplicated(keep="first")
            self.raw_data = self.raw_data.loc[~duplicate_ids].copy()
        id_removed = before - exact_removed - len(self.raw_data)
        self.cleaning_report["exact_duplicates_removed"] = int(exact_removed)
        self.cleaning_report["duplicate_ids_removed"] = int(max(id_removed, 0))
        self.cleaning_report["duplicates_removed"] = int(before - len(self.raw_data))
        return int(before - len(self.raw_data))

    def convert_data_types(self) -> pd.DataFrame:
        """Convert dates, amounts, identifiers, and boolean fields."""

        self.raw_data["Date"] = pd.to_datetime(self.raw_data["Date"], errors="coerce")
        self.raw_data["Amount"] = pd.to_numeric(self.raw_data["Amount"], errors="coerce")
        self.raw_data["Recurring"] = self._normalise_bool(self.raw_data["Recurring"])

        self.raw_data["Expense_ID"] = self.raw_data["Expense_ID"].astype("string")
        missing_id = self.raw_data["Expense_ID"].isna() | self.raw_data["Expense_ID"].str.strip().eq("")
        generated_ids = [f"EXP-{index + 1:04d}" for index in range(len(self.raw_data))]
        self.raw_data.loc[missing_id, "Expense_ID"] = np.asarray(generated_ids)[missing_id.to_numpy()]
        return self.raw_data

    def standardize_text_fields(self) -> pd.DataFrame:
        """Standardise categories, payment methods, and free-text fields."""

        category_aliases = {
            "food": "Food & Dining",
            "food and dining": "Food & Dining",
            "dining": "Food & Dining",
            "travel": "Transportation",
            "transport": "Transportation",
            "transportation": "Transportation",
            "rent": "Rent",
            "utility": "Utilities",
            "utilities": "Utilities",
        }
        known_categories = set(EXPENSE_CATEGORIES)
        self.raw_data["Category"] = self.raw_data["Category"].map(
            lambda value: category_aliases.get(str(value).strip().lower(), str(value).strip())
            if pd.notna(value)
            else "Other"
        )
        self.raw_data["Category"] = self.raw_data["Category"].map(
            lambda value: value if value in known_categories else "Other"
        )

        payment_aliases = {
            "upi": "Mobile Payment",
            "mobile": "Mobile Payment",
            "card": "Credit Card",
            "bank": "Bank Transfer",
        }
        allowed_methods = set(PAYMENT_METHODS)
        self.raw_data["Payment_Method"] = self.raw_data["Payment_Method"].map(
            lambda value: payment_aliases.get(str(value).strip().lower(), str(value).strip().title())
            if pd.notna(value)
            else "Other"
        )
        self.raw_data["Payment_Method"] = self.raw_data["Payment_Method"].map(
            lambda value: value if value in allowed_methods else "Other"
        )

        for column, default in {
            "Description": "Uncategorised expense",
            "Tags": "misc",
            "Notes": "",
        }.items():
            self.raw_data[column] = self.raw_data[column].map(
                lambda value: self._normalise_text(value, default)
            )
        return self.raw_data

    def validate_amounts(self) -> int:
        """Remove rows without a valid positive amount."""

        before = len(self.raw_data)
        invalid = self.raw_data["Amount"].isna() | (self.raw_data["Amount"] <= 0)
        self.raw_data = self.raw_data.loc[~invalid].copy()
        self.cleaning_report["invalid_amounts_removed"] = int(invalid.sum())
        self.cleaning_report["invalid_amounts_before"] = int(invalid.sum())
        self.cleaning_report["invalid_amounts"] = int(invalid.sum())
        self.cleaning_report["amount_rows_before_validation"] = int(before)
        return int(invalid.sum())

    def validate_dates(self) -> int:
        """Remove invalid, very old, or future-dated records."""

        before = len(self.raw_data)
        invalid = self.raw_data["Date"].isna()
        old = self.raw_data["Date"] < pd.Timestamp("1990-01-01")
        future = self.raw_data["Date"] > self.as_of
        remove_mask = invalid | old | future
        self.raw_data = self.raw_data.loc[~remove_mask].copy()
        self.cleaning_report["invalid_dates_removed"] = int(remove_mask.sum())
        self.cleaning_report["invalid_dates"] = int(remove_mask.sum())
        self.cleaning_report["missing_dates_removed"] = int(invalid.sum())
        self.cleaning_report["old_dates_removed"] = int(old.sum())
        self.cleaning_report["future_dates_removed"] = int(future.sum())
        self.cleaning_report["date_rows_before_validation"] = int(before)
        return int(remove_mask.sum())

    def handle_outliers(
        self,
        threshold: float = OUTLIER_THRESHOLD,
        method: str = "flag",
    ) -> pd.DataFrame:
        """Detect category-relative outliers and flag, remove, or cap them.

        Flagging is the default because an unusual expense can be valid. The
        method is intentionally explicit for teaching and testing.
        """

        if method not in {"flag", "remove", "cap"}:
            raise ValueError("method must be 'flag', 'remove', or 'cap'")
        if self.raw_data.empty:
            self.raw_data["Is_Outlier"] = pd.Series(dtype=bool)
            self.cleaning_report["outliers_detected"] = 0
            return self.raw_data

        grouped = self.raw_data.groupby("Category", observed=False)["Amount"]
        category_mean = grouped.transform("mean")
        category_std = grouped.transform("std").fillna(0)
        z_score = (self.raw_data["Amount"] - category_mean).abs().div(
            category_std.replace(0, np.nan)
        ).fillna(0)

        q1 = grouped.transform(lambda values: values.quantile(0.25))
        q3 = grouped.transform(lambda values: values.quantile(0.75))
        iqr = q3 - q1
        upper_bound = q3 + 1.5 * iqr
        outlier_mask = (z_score > threshold) | (self.raw_data["Amount"] > upper_bound)
        self.raw_data["Outlier_Z_Score"] = z_score.round(3)
        self.raw_data["Is_Outlier"] = outlier_mask.astype(bool)

        count = int(outlier_mask.sum())
        self.cleaning_report["outliers_detected"] = count
        if method == "remove" and count:
            self.raw_data = self.raw_data.loc[~outlier_mask].copy()
        elif method == "cap" and count:
            self.raw_data.loc[outlier_mask, "Amount"] = upper_bound[outlier_mask]
            self.raw_data["Amount"] = self.raw_data["Amount"].round(2)
        return self.raw_data

    def add_derived_columns(self) -> pd.DataFrame:
        """Add time, benchmark, cumulative, and spending-level features."""

        if self.raw_data.empty:
            for column, dtype in {
                "YearMonth": "string",
                "Month": "string",
                "Week": "Int64",
                "DayOfMonth": "Int64",
                "DayOfWeek": "string",
                "DayOfWeekNum": "Int64",
                "IsWeekend": bool,
                "SpendingLevel": "string",
                "CategoryAverage": float,
                "CategoryRatio": float,
                "CumulativeMonthlySpend": float,
                "Is_High_Spending": bool,
                "Is_Category_Anomaly": bool,
            }.items():
                self.raw_data[column] = pd.Series(dtype=dtype)
            return self.raw_data

        self.raw_data = self.raw_data.sort_values("Date", kind="stable").reset_index(drop=True)
        self.raw_data["YearMonth"] = self.raw_data["Date"].dt.to_period("M").astype(str)
        self.raw_data["Month"] = self.raw_data["Date"].dt.strftime("%b")
        self.raw_data["Week"] = self.raw_data["Date"].dt.isocalendar().week.astype("Int64")
        self.raw_data["DayOfMonth"] = self.raw_data["Date"].dt.day.astype("Int64")
        self.raw_data["DayOfWeek"] = self.raw_data["Date"].dt.day_name()
        self.raw_data["DayOfWeekNum"] = self.raw_data["Date"].dt.dayofweek.astype("Int64")
        self.raw_data["IsWeekend"] = self.raw_data["DayOfWeekNum"].isin([5, 6])

        q1 = float(self.raw_data["Amount"].quantile(0.25))
        q3 = float(self.raw_data["Amount"].quantile(0.75))
        self.raw_data["SpendingLevel"] = np.select(
            [self.raw_data["Amount"] <= q1, self.raw_data["Amount"] >= q3],
            ["Low", "High"],
            default="Medium",
        )
        self.raw_data["CategoryAverage"] = self.raw_data.groupby(
            "Category", observed=False
        )["Amount"].transform("mean")
        self.raw_data["CategoryRatio"] = (
            self.raw_data["Amount"] / self.raw_data["CategoryAverage"].replace(0, np.nan)
        ).fillna(0).round(3)
        self.raw_data["CumulativeMonthlySpend"] = self.raw_data.groupby("YearMonth", sort=False)[
            "Amount"
        ].cumsum().round(2)
        self.raw_data["Is_High_Spending"] = self.raw_data["Amount"] >= q3
        self.raw_data["Is_Category_Anomaly"] = self.raw_data["CategoryRatio"] >= 1.5
        return self.raw_data

    def clean_data(self, remove_outliers: bool = False) -> pd.DataFrame:
        """Run the complete quality and feature-engineering pipeline."""

        self.raw_data = self.raw_data.copy()
        initial_rows = len(self.raw_data)
        self._ensure_columns()
        self.check_missing_values()
        self.remove_duplicates()
        self.convert_data_types()
        self.standardize_text_fields()
        self.validate_amounts()
        self.validate_dates()
        self.handle_outliers(method="remove" if remove_outliers else "flag")
        self.add_derived_columns()

        self.cleaned_data = self.raw_data.reset_index(drop=True).copy()
        self.cleaning_report["initial_rows"] = int(initial_rows)
        self.cleaning_report["final_rows"] = int(len(self.cleaned_data))
        self.cleaning_report["rows_removed_total"] = int(initial_rows - len(self.cleaned_data))
        self.cleaning_report["final_missing_values"] = {
            str(column): int(count)
            for column, count in self.cleaned_data.isna().sum().items()
            if count
        }
        self.cleaning_report["data_quality_score"] = round(
            100 * len(self.cleaned_data) / initial_rows, 2
        ) if initial_rows else 100.0
        return self.cleaned_data.copy()

    def save_cleaned_data(self, filepath: Path | str = CLEANED_DATA_PATH) -> Path:
        """Save cleaned records and return the destination."""

        if self.cleaned_data is None:
            self.clean_data()
        destination = Path(filepath)
        destination.parent.mkdir(parents=True, exist_ok=True)
        self.cleaned_data.to_csv(destination, index=False)
        return destination

    def get_cleaning_report(self) -> dict[str, Any]:
        """Return a copy of the cleaning report."""

        return dict(self.cleaning_report)


def clean_expense_data(
    raw_filepath: Path | str = RAW_DATA_PATH,
    output_filepath: Path | str = CLEANED_DATA_PATH,
) -> pd.DataFrame:
    """Clean a CSV and save the result in one call."""

    cleaner = DataCleaner(filepath=raw_filepath)
    cleaned = cleaner.clean_data()
    cleaner.save_cleaned_data(output_filepath)
    return cleaned


if __name__ == "__main__":
    cleaner = DataCleaner()
    result = cleaner.clean_data()
    cleaner.save_cleaned_data()
    print(result.head().to_string(index=False))
    print(cleaner.get_cleaning_report())

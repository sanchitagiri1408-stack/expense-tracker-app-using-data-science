"""Descriptive analytics and business-friendly insight generation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.config import (
    CLEANED_DATA_PATH,
    CURRENCY,
    DAY_ORDER,
    HIGH_SPENDING_QUANTILE,
    LOW_SPENDING_QUANTILE,
    OVERSPENDING_RATIO,
    format_currency,
)


class ExpenseAnalyzer:
    """Calculate KPIs, summary tables, spending patterns, and insights."""

    def __init__(
        self,
        data: pd.DataFrame | None = None,
        filepath: Path | str = CLEANED_DATA_PATH,
        currency: str = CURRENCY,
    ) -> None:
        if data is not None:
            self.data = data.copy()
        else:
            self.data = pd.read_csv(filepath)
        if not self.data.empty:
            self.data["Date"] = pd.to_datetime(self.data["Date"], errors="coerce")
            self.data["Amount"] = pd.to_numeric(self.data["Amount"], errors="coerce")
            self.data = self.data.dropna(subset=["Date", "Amount"]).copy()
        self.currency = currency
        self.statistics: dict[str, Any] = {}
        self.tables: dict[str, pd.DataFrame] = {}
        self.insights: list[str] = []

    def calculate_basic_statistics(self) -> dict[str, Any]:
        """Return the top-level KPI dictionary."""

        if self.data.empty:
            self.statistics = {
                "total_expenses": 0.0,
                "average_transaction": 0.0,
                "median_transaction": 0.0,
                "std_deviation": 0.0,
                "min_transaction": 0.0,
                "max_transaction": 0.0,
                "transaction_count": 0,
                "unique_categories": 0,
                "unique_payment_methods": 0,
                "date_range_days": 0,
                "average_daily_spending": 0.0,
                "weekend_spend_percentage": 0.0,
            }
            return dict(self.statistics)

        date_range_days = int((self.data["Date"].max() - self.data["Date"].min()).days + 1)
        total = float(self.data["Amount"].sum())
        weekend_spend = float(self.data.loc[self._weekend_mask(), "Amount"].sum())
        self.statistics = {
            "total_expenses": round(total, 2),
            "average_transaction": round(float(self.data["Amount"].mean()), 2),
            "median_transaction": round(float(self.data["Amount"].median()), 2),
            "std_deviation": round(float(self.data["Amount"].std(ddof=0)), 2),
            "min_transaction": round(float(self.data["Amount"].min()), 2),
            "max_transaction": round(float(self.data["Amount"].max()), 2),
            "transaction_count": int(len(self.data)),
            "unique_categories": int(self.data["Category"].nunique()),
            "unique_payment_methods": int(self.data["Payment_Method"].nunique()),
            "date_range_days": date_range_days,
            "average_daily_spending": round(total / date_range_days, 2),
            "weekend_spend_percentage": round((weekend_spend / total * 100) if total else 0, 2),
            "start_date": self.data["Date"].min().date().isoformat(),
            "end_date": self.data["Date"].max().date().isoformat(),
        }
        return dict(self.statistics)

    def _weekend_mask(self) -> pd.Series:
        """Return a weekend mask whether or not feature engineering ran."""

        if "IsWeekend" in self.data.columns:
            return self.data["IsWeekend"].astype(bool)
        return self.data["Date"].dt.dayofweek >= 5

    def _year_month(self) -> pd.Series:
        """Return a stable YYYY-MM grouping key."""

        if "YearMonth" in self.data.columns:
            return self.data["YearMonth"].astype(str)
        return self.data["Date"].dt.to_period("M").astype(str)

    def category_analysis(self) -> pd.DataFrame:
        """Summarise total, average, count, and share by category."""

        total = float(self.data["Amount"].sum()) if not self.data.empty else 0.0
        if self.data.empty:
            table = pd.DataFrame(columns=["Category", "Total", "Average", "Count", "Percentage"])
        else:
            table = (
                self.data.groupby("Category", as_index=False, observed=True)["Amount"]
                .agg(Total="sum", Average="mean", Count="count")
                .sort_values("Total", ascending=False)
            )
            table["Percentage"] = np.where(
                total > 0, table["Total"] / total * 100, 0
            )
            table[["Total", "Average", "Percentage"]] = table[
                ["Total", "Average", "Percentage"]
            ].round(2)
        self.tables["category_summary"] = table.reset_index(drop=True)
        return self.tables["category_summary"].copy()

    def payment_method_analysis(self) -> pd.DataFrame:
        """Summarise total and transaction count by payment method."""

        total = float(self.data["Amount"].sum()) if not self.data.empty else 0.0
        if self.data.empty:
            table = pd.DataFrame(columns=["Payment_Method", "Total", "Average", "Count", "Percentage"])
        else:
            table = (
                self.data.groupby("Payment_Method", as_index=False, observed=True)["Amount"]
                .agg(Total="sum", Average="mean", Count="count")
                .sort_values("Total", ascending=False)
            )
            table["Percentage"] = np.where(
                total > 0, table["Total"] / total * 100, 0
            )
            table[["Total", "Average", "Percentage"]] = table[
                ["Total", "Average", "Percentage"]
            ].round(2)
        self.tables["payment_summary"] = table.reset_index(drop=True)
        return self.tables["payment_summary"].copy()

    def temporal_analysis(self) -> dict[str, pd.DataFrame]:
        """Build daily, weekly, and monthly spending tables."""

        if self.data.empty:
            daily = pd.DataFrame(columns=["Date", "Daily_Total", "Transaction_Count", "Daily_Average"])
            weekly = pd.DataFrame(columns=["Week", "Weekly_Total", "Transaction_Count", "Weekly_Average"])
            monthly = pd.DataFrame(
                columns=["YearMonth", "Monthly_Total", "Transaction_Count", "Monthly_Average", "MoM_Change_Pct"]
            )
        else:
            daily = (
                self.data.assign(DateOnly=self.data["Date"].dt.date)
                .groupby("DateOnly", as_index=False)["Amount"]
                .agg(Daily_Total="sum", Transaction_Count="count", Daily_Average="mean")
                .rename(columns={"DateOnly": "Date"})
            )
            daily[["Daily_Total", "Daily_Average"]] = daily[["Daily_Total", "Daily_Average"]].round(2)

            work = self.data.assign(Week=self.data["Date"].dt.to_period("W").astype(str))
            weekly = (
                work.groupby("Week", as_index=False)["Amount"]
                .agg(Weekly_Total="sum", Transaction_Count="count", Weekly_Average="mean")
            )
            weekly[["Weekly_Total", "Weekly_Average"]] = weekly[["Weekly_Total", "Weekly_Average"]].round(2)

            monthly = (
                self.data.assign(YearMonth=self._year_month())
                .groupby("YearMonth", as_index=False)["Amount"]
                .agg(Monthly_Total="sum", Transaction_Count="count", Monthly_Average="mean")
                .sort_values("YearMonth")
            )
            monthly[["Monthly_Total", "Monthly_Average"]] = monthly[
                ["Monthly_Total", "Monthly_Average"]
            ].round(2)
            monthly["MoM_Change_Pct"] = monthly["Monthly_Total"].pct_change().mul(100).round(2)
            monthly["MoM_Change_Pct"] = monthly["MoM_Change_Pct"].replace([np.inf, -np.inf], np.nan).fillna(0)

        self.tables["daily_summary"] = daily.reset_index(drop=True)
        self.tables["weekly_summary"] = weekly.reset_index(drop=True)
        self.tables["monthly_summary"] = monthly.reset_index(drop=True)
        return {
            "daily": self.tables["daily_summary"].copy(),
            "weekly": self.tables["weekly_summary"].copy(),
            "monthly": self.tables["monthly_summary"].copy(),
        }

    def day_of_week_analysis(self) -> pd.DataFrame:
        """Compare spending by weekday in calendar order."""

        if self.data.empty:
            table = pd.DataFrame(columns=["DayOfWeek", "Total", "Average", "Count"])
        else:
            work = self.data.assign(DayOfWeek=self.data["Date"].dt.day_name())
            table = (
                work.groupby("DayOfWeek", as_index=False)["Amount"]
                .agg(Total="sum", Average="mean", Count="count")
            )
            table["DayOfWeek"] = pd.Categorical(table["DayOfWeek"], categories=DAY_ORDER, ordered=True)
            table = table.sort_values("DayOfWeek")
            table[["Total", "Average"]] = table[["Total", "Average"]].round(2)
            table["DayOfWeek"] = table["DayOfWeek"].astype(str)
        self.tables["day_of_week_summary"] = table.reset_index(drop=True)
        return self.tables["day_of_week_summary"].copy()

    def recurring_analysis(self) -> pd.DataFrame:
        """Compare recurring and one-off expense records."""

        if "Recurring" not in self.data.columns:
            self.data["Recurring"] = False
        total = float(self.data["Amount"].sum()) if not self.data.empty else 0.0
        table = (
            self.data.assign(Expense_Type=np.where(self.data["Recurring"], "Recurring", "Non-Recurring"))
            .groupby("Expense_Type", as_index=False)["Amount"]
            .agg(Total="sum", Average="mean", Count="count")
        )
        if not table.empty:
            table["Percentage"] = np.where(total > 0, table["Total"] / total * 100, 0)
            table[["Total", "Average", "Percentage"]] = table[
                ["Total", "Average", "Percentage"]
            ].round(2)
        self.tables["recurring_summary"] = table.reset_index(drop=True)
        return self.tables["recurring_summary"].copy()

    def spending_distribution(self) -> dict[str, float]:
        """Return useful amount percentiles."""

        if self.data.empty:
            result = {"q25": 0.0, "median": 0.0, "q75": 0.0, "q90": 0.0, "q95": 0.0}
        else:
            values = self.data["Amount"].quantile([0.25, 0.50, 0.75, 0.90, 0.95])
            result = {
                "q25": round(float(values.loc[0.25]), 2),
                "median": round(float(values.loc[0.50]), 2),
                "q75": round(float(values.loc[0.75]), 2),
                "q90": round(float(values.loc[0.90]), 2),
                "q95": round(float(values.loc[0.95]), 2),
            }
        self.statistics["distribution"] = result
        return dict(result)

    def high_low_spending_analysis(self) -> dict[str, Any]:
        """Describe the upper and lower transaction quartiles."""

        if self.data.empty:
            result = {
                "high_threshold": 0.0,
                "high_count": 0,
                "high_total": 0.0,
                "low_threshold": 0.0,
                "low_count": 0,
                "low_total": 0.0,
            }
        else:
            high_threshold = float(self.data["Amount"].quantile(HIGH_SPENDING_QUANTILE))
            low_threshold = float(self.data["Amount"].quantile(LOW_SPENDING_QUANTILE))
            high = self.data[self.data["Amount"] >= high_threshold]
            low = self.data[self.data["Amount"] <= low_threshold]
            result = {
                "high_threshold": round(high_threshold, 2),
                "high_count": int(len(high)),
                "high_total": round(float(high["Amount"].sum()), 2),
                "low_threshold": round(low_threshold, 2),
                "low_count": int(len(low)),
                "low_total": round(float(low["Amount"].sum()), 2),
            }
        self.statistics["high_low"] = result
        return dict(result)

    def category_daily_average(self) -> pd.DataFrame:
        """Return category totals and averages per calendar day."""

        days = self.statistics.get("date_range_days", 0) or 1
        table = self.category_analysis()[["Category", "Total"]].copy()
        table["Daily_Average"] = (table["Total"] / days).round(2)
        self.tables["category_daily_summary"] = table
        return table.copy()

    def identify_anomalies(self) -> dict[str, Any]:
        """Return flagged records and the transaction extremes."""

        flagged = (
            self.data[self.data.get("Is_Outlier", pd.Series(False, index=self.data.index))]
            .sort_values("Amount", ascending=False)
            if not self.data.empty
            else self.data.copy()
        )
        result: dict[str, Any] = {
            "flagged_count": int(len(flagged)),
            "flagged_total": round(float(flagged["Amount"].sum()), 2) if not flagged.empty else 0.0,
            "flagged_records": flagged.head(10).copy(),
        }
        if not self.data.empty:
            highest = self.data.loc[self.data["Amount"].idxmax()]
            lowest = self.data.loc[self.data["Amount"].idxmin()]
            result["highest_transaction"] = {
                "amount": round(float(highest["Amount"]), 2),
                "category": str(highest["Category"]),
                "date": pd.Timestamp(highest["Date"]).date().isoformat(),
                "description": str(highest.get("Description", "")),
            }
            result["lowest_transaction"] = {
                "amount": round(float(lowest["Amount"]), 2),
                "category": str(lowest["Category"]),
                "date": pd.Timestamp(lowest["Date"]).date().isoformat(),
                "description": str(lowest.get("Description", "")),
            }
        self.tables["anomaly_records"] = flagged.copy()
        self.statistics["anomalies"] = result
        return result

    def overspending_analysis(self) -> dict[str, pd.DataFrame | float]:
        """Flag months and categories that exceed a simple baseline.

        The baseline is an educational rule, not a personal financial budget.
        A production version should use a user-provided budget and a defined
        reporting period.
        """

        monthly = self.tables.get("monthly_summary", pd.DataFrame()).copy()
        if monthly.empty:
            monthly["Baseline"] = pd.Series(dtype=float)
            monthly["Is_Overspending"] = pd.Series(dtype=bool)
            category = pd.DataFrame(columns=["Category", "Monthly_Average", "Peak_Monthly_Total", "Is_Above_Baseline"])
            baseline = 0.0
        else:
            baseline = float(monthly["Monthly_Total"].mean())
            monthly["Baseline"] = round(baseline, 2)
            monthly["Is_Overspending"] = monthly["Monthly_Total"] > baseline * OVERSPENDING_RATIO
            category_month = (
                self.data.assign(YearMonth=self._year_month())
                .groupby(["Category", "YearMonth"], as_index=False)["Amount"]
                .sum()
            )
            category = (
                category_month.groupby("Category", as_index=False)["Amount"]
                .agg(Monthly_Average="mean", Peak_Monthly_Total="max")
            )
            category["Is_Above_Baseline"] = category["Peak_Monthly_Total"] > category["Monthly_Average"] * OVERSPENDING_RATIO
            category[["Monthly_Average", "Peak_Monthly_Total"]] = category[
                ["Monthly_Average", "Peak_Monthly_Total"]
            ].round(2)
        self.tables["monthly_overspending"] = monthly
        self.tables["category_overspending"] = category.reset_index(drop=True)
        self.statistics["monthly_baseline"] = round(baseline, 2)
        return {
            "monthly": monthly.copy(),
            "category": category.reset_index(drop=True).copy(),
            "baseline": float(baseline),
        }

    def correlation_analysis(self) -> pd.DataFrame:
        """Return a small correlation table for numeric time features."""

        if self.data.empty:
            table = pd.DataFrame()
        else:
            work = pd.DataFrame(
                {
                    "Amount": self.data["Amount"],
                    "DayOfMonth": self.data["Date"].dt.day,
                    "MonthNumber": self.data["Date"].dt.month,
                    "DayOfWeekNumber": self.data["Date"].dt.dayofweek,
                }
            )
            table = work.corr(numeric_only=True).round(3)
        self.tables["correlation_matrix"] = table
        return table.copy()

    def generate_insights(self) -> list[str]:
        """Create cautious, quantified observations for the dashboard/report."""

        if not self.statistics:
            self.calculate_basic_statistics()
        if "category_summary" not in self.tables:
            self.category_analysis()
        if "monthly_summary" not in self.tables:
            self.temporal_analysis()
        if "day_of_week_summary" not in self.tables:
            self.day_of_week_analysis()
        if "monthly_overspending" not in self.tables:
            self.overspending_analysis()
        if "anomalies" not in self.statistics:
            self.identify_anomalies()

        if not self.data.empty:
            category = self.tables["category_summary"].iloc[0]
            month = self.tables["monthly_summary"].sort_values("Monthly_Total", ascending=False).iloc[0]
            day = self.tables["day_of_week_summary"].sort_values("Total", ascending=False).iloc[0]
            top_method = self.tables.get("payment_summary", pd.DataFrame())
            messages = [
                f"The synthetic sample contains {self.statistics['transaction_count']:,} transactions totaling {format_currency(self.statistics['total_expenses'], self.currency)}.",
                f"{category['Category']} is the largest category at {format_currency(category['Total'], self.currency)} ({category['Percentage']:.1f}% of total spend).",
                f"{month['YearMonth']} is the peak month at {format_currency(month['Monthly_Total'], self.currency)} in this generated sample.",
                f"{day['DayOfWeek']} has the highest observed total spending at {format_currency(day['Total'], self.currency)}.",
                f"Weekend transactions represent {self.statistics['weekend_spend_percentage']:.1f}% of total spend; use this as a planning signal, not a universal behavioral claim.",
            ]
            overspending_months = self.tables["monthly_overspending"]
            flagged_months = overspending_months.loc[overspending_months["Is_Overspending"], "YearMonth"].tolist()
            if flagged_months:
                messages.append(
                    "Months above the simple educational baseline: " + ", ".join(map(str, flagged_months)) + "."
                )
            else:
                messages.append("No month crossed the simple educational overspending baseline.")
            anomaly_count = int(self.statistics["anomalies"]["flagged_count"])
            messages.append(
                f"{anomaly_count} transaction(s) were flagged for review using a category-relative outlier rule; flags do not imply fraud."
            )
            if not top_method.empty:
                method = top_method.iloc[0]
                messages.append(
                    f"{method['Payment_Method']} is the largest payment channel by value at {format_currency(method['Total'], self.currency)}."
                )
            self.insights = messages
        else:
            self.insights = ["No transactions are available for analysis."]
        return list(self.insights)

    def generate_summary_report(self) -> str:
        """Return a plain-text summary suitable for saving to a report."""

        if not self.insights:
            self.generate_insights()
        lines = [
            "EXPENSE TRACKER — SYNTHETIC DATA ANALYSIS REPORT",
            "=" * 52,
            "This report describes generated demo data. It is not financial advice.",
            "",
            f"Date range: {self.statistics.get('start_date', 'n/a')} to {self.statistics.get('end_date', 'n/a')}",
            f"Transactions: {self.statistics.get('transaction_count', 0):,}",
            f"Total spend: {format_currency(self.statistics.get('total_expenses', 0), self.currency)}",
            f"Average transaction: {format_currency(self.statistics.get('average_transaction', 0), self.currency)}",
            f"Median transaction: {format_currency(self.statistics.get('median_transaction', 0), self.currency)}",
            "",
            "KEY INSIGHTS",
            "- " + "\n- ".join(self.insights),
            "",
            "NEXT QUESTIONS",
            "- Compare the sample with a user-defined budget and reporting period.",
            "- Review every flagged transaction using source context before taking action.",
        ]
        return "\n".join(lines) + "\n"

    def analyze_all(self) -> dict[str, pd.DataFrame]:
        """Run all analysis steps and return generated tables."""

        self.calculate_basic_statistics()
        self.category_analysis()
        self.payment_method_analysis()
        self.temporal_analysis()
        self.day_of_week_analysis()
        self.recurring_analysis()
        self.spending_distribution()
        self.high_low_spending_analysis()
        self.category_daily_average()
        self.identify_anomalies()
        self.overspending_analysis()
        self.correlation_analysis()
        self.generate_insights()
        return {name: table.copy() for name, table in self.tables.items()}

    def get_insights(self) -> list[str]:
        """Return generated insight messages."""

        return list(self.insights)

    def get_statistics(self) -> dict[str, Any]:
        """Return generated KPI values."""

        return dict(self.statistics)


def analyze_expenses(filepath: Path | str = CLEANED_DATA_PATH) -> tuple[ExpenseAnalyzer, dict[str, pd.DataFrame]]:
    """Load a cleaned CSV and run the complete analysis."""

    analyzer = ExpenseAnalyzer(filepath=filepath)
    return analyzer, analyzer.analyze_all()


if __name__ == "__main__":
    analyzer, _ = analyze_expenses()
    print(analyzer.generate_summary_report())

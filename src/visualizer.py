"""Static Matplotlib/Seaborn and interactive Plotly visualizations."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from src.config import (
    CATEGORY_COLORS,
    CHARTS_DIR,
    CURRENCY,
    DAY_ORDER,
    FIGURE_DPI,
    FIGURE_SIZE,
    PLOT_STYLE,
    format_currency,
)


class ExpenseVisualizer:
    """Create reproducible static chart files and dashboard figures."""

    def __init__(
        self,
        data: pd.DataFrame | None = None,
        output_dir: Path | str = CHARTS_DIR,
        currency: str = CURRENCY,
    ) -> None:
        self.data = data.copy() if data is not None else pd.DataFrame()
        if not self.data.empty:
            self.data["Date"] = pd.to_datetime(self.data["Date"], errors="coerce")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.currency = currency
        plt.style.use(PLOT_STYLE)
        sns.set_theme(style="whitegrid", palette="deep")

    def set_data(self, data: pd.DataFrame) -> None:
        """Replace the data used for visualizations."""

        self.data = data.copy()
        if not self.data.empty:
            self.data["Date"] = pd.to_datetime(self.data["Date"], errors="coerce")

    def _save(self, figure: plt.Figure, filename: str, save: bool) -> Path | None:
        """Save and close a Matplotlib figure without opening a GUI window."""

        destination = self.output_dir / filename
        if save:
            figure.savefig(destination, dpi=FIGURE_DPI, bbox_inches="tight")
        plt.close(figure)
        return destination if save else None

    def _category_totals(self) -> pd.Series:
        if self.data.empty:
            return pd.Series(dtype=float)
        return self.data.groupby("Category", observed=True)["Amount"].sum().sort_values(ascending=False)

    def create_category_pie_chart(self, save: bool = True) -> Path | None:
        """Show how total spending is distributed by category."""

        totals = self._category_totals()
        if totals.empty:
            return None
        figure, axis = plt.subplots(figsize=FIGURE_SIZE, dpi=FIGURE_DPI)
        colors = [CATEGORY_COLORS.get(category, "#adb5bd") for category in totals.index]
        axis.pie(
            totals.values,
            labels=totals.index,
            autopct="%1.1f%%",
            startangle=90,
            colors=colors,
            wedgeprops={"linewidth": 1, "edgecolor": "white"},
        )
        axis.set_title("Synthetic Expense Distribution by Category", fontweight="bold")
        figure.text(0.5, 0.01, "Portfolio demo data — not financial advice", ha="center", fontsize=8)
        figure.tight_layout()
        return self._save(figure, "01_category_pie_chart.png", save)

    def create_category_bar_chart(self, save: bool = True) -> Path | None:
        """Compare total spend across categories."""

        totals = self._category_totals().sort_values()
        if totals.empty:
            return None
        figure, axis = plt.subplots(figsize=FIGURE_SIZE, dpi=FIGURE_DPI)
        colors = [CATEGORY_COLORS.get(category, "#adb5bd") for category in totals.index]
        bars = axis.barh(totals.index, totals.values, color=colors)
        axis.set_xlabel(f"Total spending ({self.currency})")
        axis.set_title("Total Spending by Category", fontweight="bold")
        for bar, value in zip(bars, totals.values):
            axis.text(value, bar.get_y() + bar.get_height() / 2, f" {value:,.0f}", va="center", fontsize=9)
        figure.tight_layout()
        return self._save(figure, "02_category_bar_chart.png", save)

    def create_monthly_trend_line(self, save: bool = True) -> Path | None:
        """Plot monthly totals and the mean monthly baseline."""

        if self.data.empty:
            return None
        monthly = (
            self.data.assign(YearMonth=self.data["Date"].dt.to_period("M").astype(str))
            .groupby("YearMonth", as_index=False)["Amount"]
            .sum()
            .sort_values("YearMonth")
        )
        figure, axis = plt.subplots(figsize=FIGURE_SIZE, dpi=FIGURE_DPI)
        axis.plot(monthly["YearMonth"], monthly["Amount"], marker="o", linewidth=2.5, color="#264653")
        axis.axhline(monthly["Amount"].mean(), linestyle="--", color="#e76f51", label="Average month")
        axis.set_xlabel("Month")
        axis.set_ylabel(f"Total spending ({self.currency})")
        axis.set_title("Monthly Spending Trend", fontweight="bold")
        axis.tick_params(axis="x", rotation=35)
        axis.legend()
        for index, value in enumerate(monthly["Amount"]):
            axis.annotate(f"{value:,.0f}", (index, value), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8)
        figure.tight_layout()
        return self._save(figure, "03_monthly_trend.png", save)

    def create_daily_pattern_heatmap(self, save: bool = True) -> Path | None:
        """Display spending by weekday and month as a heatmap."""

        if self.data.empty:
            return None
        work = self.data.assign(
            DayOfWeek=self.data["Date"].dt.day_name(),
            YearMonth=self.data["Date"].dt.to_period("M").astype(str),
        )
        pivot = work.pivot_table(
            values="Amount",
            index="DayOfWeek",
            columns="YearMonth",
            aggfunc="sum",
            fill_value=0,
        ).reindex([day for day in DAY_ORDER if day in work["DayOfWeek"].unique()])
        figure, axis = plt.subplots(figsize=(12, 6), dpi=FIGURE_DPI)
        sns.heatmap(pivot, cmap="YlOrRd", annot=True, fmt=",.0f", linewidths=0.5, ax=axis, cbar_kws={"label": self.currency})
        axis.set_title("Spending Heatmap: Day of Week vs Month", fontweight="bold")
        axis.set_xlabel("Month")
        axis.set_ylabel("Day of week")
        figure.tight_layout()
        return self._save(figure, "04_daily_heatmap.png", save)

    def create_payment_method_distribution(self, save: bool = True) -> Path | None:
        """Compare payment channels by value and transaction count."""

        if self.data.empty:
            return None
        payment = self.data.groupby("Payment_Method", observed=True)["Amount"].agg(["sum", "count"]).sort_values("sum")
        figure, axes = plt.subplots(1, 2, figsize=(14, 5), dpi=FIGURE_DPI)
        axes[0].barh(payment.index, payment["sum"], color="#2a9d8f")
        axes[0].set_title("Spend by Payment Method", fontweight="bold")
        axes[0].set_xlabel(f"Amount ({self.currency})")
        axes[1].barh(payment.index, payment["count"], color="#f4a261")
        axes[1].set_title("Transaction Count by Payment Method", fontweight="bold")
        axes[1].set_xlabel("Transactions")
        figure.tight_layout()
        return self._save(figure, "05_payment_distribution.png", save)

    def create_amount_distribution_histogram(self, save: bool = True) -> Path | None:
        """Show the skew and spread of transaction amounts."""

        if self.data.empty:
            return None
        figure, axis = plt.subplots(figsize=FIGURE_SIZE, dpi=FIGURE_DPI)
        axis.hist(self.data["Amount"], bins=35, color="#457b9d", alpha=0.85, edgecolor="white")
        axis.axvline(self.data["Amount"].mean(), color="#e76f51", linestyle="--", label="Mean")
        axis.axvline(self.data["Amount"].median(), color="#2a9d8f", linestyle="--", label="Median")
        axis.set_title("Distribution of Transaction Amounts", fontweight="bold")
        axis.set_xlabel(f"Amount ({self.currency})")
        axis.set_ylabel("Transaction count")
        axis.legend()
        figure.tight_layout()
        return self._save(figure, "06_amount_histogram.png", save)

    def create_day_of_week_analysis(self, save: bool = True) -> Path | None:
        """Compare totals, counts, and average transaction value by weekday."""

        if self.data.empty:
            return None
        work = self.data.assign(DayOfWeek=self.data["Date"].dt.day_name())
        summary = work.groupby("DayOfWeek", observed=True)["Amount"].agg(["sum", "count", "mean"]).reindex(DAY_ORDER).dropna(how="all")
        figure, axes = plt.subplots(1, 3, figsize=(17, 5), dpi=FIGURE_DPI)
        labels = summary.index.tolist()
        axes[0].bar(labels, summary["sum"], color="#264653")
        axes[0].set_title("Total Spend")
        axes[0].set_ylabel(f"Amount ({self.currency})")
        axes[1].bar(labels, summary["count"], color="#2a9d8f")
        axes[1].set_title("Transaction Count")
        axes[2].bar(labels, summary["mean"], color="#e9c46a")
        axes[2].set_title("Average Transaction")
        for axis in axes:
            axis.tick_params(axis="x", rotation=45)
            axis.grid(axis="y", alpha=0.25)
        figure.suptitle("Spending Patterns by Day of Week", fontweight="bold")
        figure.tight_layout()
        return self._save(figure, "07_day_of_week_analysis.png", save)

    def create_category_month_heatmap(self, save: bool = True) -> Path | None:
        """Show category totals across months for presentation evidence."""

        if self.data.empty:
            return None
        work = self.data.assign(YearMonth=self.data["Date"].dt.to_period("M").astype(str))
        pivot = work.pivot_table(values="Amount", index="Category", columns="YearMonth", aggfunc="sum", fill_value=0)
        pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=False).index]
        figure, axis = plt.subplots(figsize=(12, 6), dpi=FIGURE_DPI)
        sns.heatmap(pivot, cmap="Blues", annot=True, fmt=",.0f", linewidths=0.5, ax=axis, cbar_kws={"label": self.currency})
        axis.set_title("Category Spending by Month", fontweight="bold")
        axis.set_xlabel("Month")
        axis.set_ylabel("Category")
        figure.tight_layout()
        return self._save(figure, "08_category_month_heatmap.png", save)

    def create_interactive_category_pie(self) -> Any:
        """Return a Plotly category pie for Streamlit."""

        import plotly.graph_objects as go

        totals = self._category_totals()
        figure = go.Figure(
            data=[
                go.Pie(
                    labels=totals.index.tolist(),
                    values=totals.values.tolist(),
                    hole=0.35,
                    marker={"colors": [CATEGORY_COLORS.get(name, "#adb5bd") for name in totals.index]},
                )
            ]
        )
        figure.update_layout(title="Spending Distribution by Category", margin={"t": 60, "l": 20, "r": 20, "b": 20})
        return figure

    def create_interactive_monthly_trend(self) -> Any:
        """Return a Plotly monthly trend for Streamlit."""

        import plotly.express as px

        monthly = (
            self.data.assign(YearMonth=self.data["Date"].dt.to_period("M").astype(str))
            .groupby("YearMonth", as_index=False)["Amount"]
            .sum()
            .sort_values("YearMonth")
        )
        figure = px.line(monthly, x="YearMonth", y="Amount", markers=True, title="Monthly Spending Trend")
        figure.update_layout(yaxis_title=f"Amount ({self.currency})", xaxis_title="Month")
        return figure

    def create_interactive_category_bar(self) -> Any:
        """Return an interactive category comparison chart."""

        import plotly.express as px

        totals = self._category_totals().reset_index()
        totals.columns = ["Category", "Amount"]
        figure = px.bar(totals, x="Category", y="Amount", color="Category", title="Total Spending by Category", color_discrete_map=CATEGORY_COLORS)
        figure.update_layout(showlegend=False, yaxis_title=f"Amount ({self.currency})")
        return figure

    def create_kpi_cards(self) -> dict[str, str]:
        """Return formatted metrics for a dashboard."""

        if self.data.empty:
            return {
                "Total Spending": format_currency(0, self.currency),
                "Average Transaction": format_currency(0, self.currency),
                "Highest Transaction": format_currency(0, self.currency),
                "Transaction Count": "0",
            }
        date_range = (self.data["Date"].max() - self.data["Date"].min()).days + 1
        return {
            "Total Spending": format_currency(self.data["Amount"].sum(), self.currency),
            "Average Transaction": format_currency(self.data["Amount"].mean(), self.currency),
            "Average Daily Spending": format_currency(self.data["Amount"].sum() / date_range, self.currency),
            "Highest Transaction": format_currency(self.data["Amount"].max(), self.currency),
            "Transaction Count": f"{len(self.data):,}",
        }

    def visualize_all(self) -> dict[str, Path]:
        """Generate the complete static evidence set."""

        creators = {
            "category_pie": self.create_category_pie_chart,
            "category_bar": self.create_category_bar_chart,
            "monthly_trend": self.create_monthly_trend_line,
            "daily_heatmap": self.create_daily_pattern_heatmap,
            "payment_distribution": self.create_payment_method_distribution,
            "amount_histogram": self.create_amount_distribution_histogram,
            "day_of_week": self.create_day_of_week_analysis,
            "category_month_heatmap": self.create_category_month_heatmap,
        }
        generated: dict[str, Path] = {}
        for name, creator in creators.items():
            path = creator(save=True)
            if path is not None:
                generated[name] = path
        return generated


def visualize_expenses(data: pd.DataFrame, output_dir: Path | str = CHARTS_DIR) -> ExpenseVisualizer:
    """Generate all static charts and return the visualizer."""

    visualizer = ExpenseVisualizer(data, output_dir=output_dir)
    visualizer.visualize_all()
    return visualizer


if __name__ == "__main__":
    from src.data_cleaner import DataCleaner
    from src.data_generator import DataGenerator

    raw = DataGenerator().generate_data()
    clean = DataCleaner(data=raw).clean_data()
    paths = ExpenseVisualizer(clean).visualize_all()
    print("Generated charts:")
    for path in paths.values():
        print(path)

"""Generate reproducible synthetic expense data.

The generator is deliberately transparent. It creates a small number of
recurring rent rows, then fills the remaining period with daily expenses whose
categories, dates, and amounts vary. The result is safe to publish because it
does not represent a real person's finances.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from src.config import (
    CATEGORY_AMOUNT_RANGES,
    END_DATE,
    EXPENSE_CATEGORIES,
    NUM_RECORDS,
    PAYMENT_METHOD_DISTRIBUTION,
    RANDOM_SEED,
    RAW_DATA_PATH,
    START_DATE,
)


class DataGenerator:
    """Create deterministic, realistic-looking expense records."""

    def __init__(
        self,
        num_records: int = NUM_RECORDS,
        seed: int = RANDOM_SEED,
        start_date: date | str = START_DATE,
        end_date: date | str = END_DATE,
        outlier_fraction: float = 0.03,
    ) -> None:
        if int(num_records) < 0:
            raise ValueError("num_records must be non-negative")
        if not 0 <= float(outlier_fraction) <= 1:
            raise ValueError("outlier_fraction must be between 0 and 1")

        self.num_records = int(num_records)
        self.seed = int(seed)
        self.start_date = pd.Timestamp(start_date).normalize()
        self.end_date = pd.Timestamp(end_date).normalize()
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        self.outlier_fraction = float(outlier_fraction)
        self.rng = np.random.default_rng(self.seed)
        self.data: pd.DataFrame | None = None

    def _reset_rng(self) -> None:
        """Reset the local RNG so repeated calls are identical."""

        self.rng = np.random.default_rng(self.seed)

    def generate_dates(self, count: int | None = None) -> list[pd.Timestamp]:
        """Generate dates in the inclusive date range.

        Weekend dates receive a slightly higher probability to make the
        sample useful for day-of-week analysis without claiming a real-world
        behavioral pattern.
        """

        count = self.num_records if count is None else int(count)
        if count <= 0:
            return []

        date_range = pd.date_range(self.start_date, self.end_date, freq="D")
        weights = np.array(
            [1.6 if timestamp.dayofweek >= 5 else 1.0 for timestamp in date_range],
            dtype=float,
        )
        weights /= weights.sum()
        selected = self.rng.choice(date_range.to_numpy(), size=count, p=weights)
        return sorted(pd.Timestamp(value).normalize() for value in selected)

    def generate_categories(self, count: int | None = None) -> np.ndarray:
        """Sample categories from configured probabilities."""

        count = self.num_records if count is None else int(count)
        categories = list(EXPENSE_CATEGORIES)
        probabilities = np.asarray(list(EXPENSE_CATEGORIES.values()), dtype=float)
        probabilities /= probabilities.sum()
        return self.rng.choice(categories, size=count, p=probabilities)

    def _non_rent_categories(self, count: int) -> np.ndarray:
        """Sample variable categories while reserving rent for fixed rows."""

        categories = [name for name in EXPENSE_CATEGORIES if name != "Rent"]
        probabilities = np.asarray(
            [EXPENSE_CATEGORIES[name] for name in categories], dtype=float
        )
        probabilities /= probabilities.sum()
        return self.rng.choice(categories, size=count, p=probabilities)

    def generate_amounts(
        self,
        categories: Iterable[str],
        dates: Iterable[pd.Timestamp] | None = None,
    ) -> list[float]:
        """Generate positively skewed amounts for each category."""

        category_values = list(categories)
        date_values = list(dates) if dates is not None else [None] * len(category_values)
        amounts: list[float] = []
        for position, category in enumerate(category_values):
            minimum, maximum = CATEGORY_AMOUNT_RANGES.get(
                str(category), CATEGORY_AMOUNT_RANGES["Other"]
            )
            if category == "Rent":
                amount = self.rng.normal(loc=(minimum + maximum) / 2, scale=350)
            else:
                scale = max((maximum - minimum) / 3.5, 1.0)
                amount = minimum + self.rng.gamma(shape=2.2, scale=scale)
                if date_values[position] is not None:
                    timestamp = pd.Timestamp(date_values[position])
                    # A small synthetic seasonal effect creates a visible but
                    # not deterministic-looking monthly comparison.
                    if timestamp.month in {3, 6} and category in {
                        "Shopping",
                        "Entertainment",
                    }:
                        amount *= 1.12
                    if timestamp.dayofweek >= 5 and category == "Food & Dining":
                        amount *= 1.10
            amounts.append(round(float(np.clip(amount, minimum, maximum)), 2))
        return amounts

    def generate_payment_methods(self, count: int | None = None) -> np.ndarray:
        """Sample payment methods from configured probabilities."""

        count = self.num_records if count is None else int(count)
        methods = list(PAYMENT_METHOD_DISTRIBUTION)
        probabilities = np.asarray(list(PAYMENT_METHOD_DISTRIBUTION.values()), dtype=float)
        probabilities /= probabilities.sum()
        return self.rng.choice(methods, size=count, p=probabilities)

    def generate_descriptions(self, categories: Iterable[str]) -> list[str]:
        """Create descriptions that match each category."""

        templates = {
            "Rent": ["Monthly rent"],
            "Food & Dining": ["Lunch", "Groceries", "Coffee", "Dinner", "Takeaway"],
            "Transportation": ["Fuel", "Taxi ride", "Bus pass", "Parking", "Metro"],
            "Entertainment": ["Movie tickets", "Streaming", "Concert", "Gaming", "Books"],
            "Shopping": ["Online purchase", "Clothing", "Electronics", "Home goods"],
            "Utilities": ["Electricity bill", "Internet bill", "Phone bill", "Gas bill"],
            "Healthcare": ["Pharmacy", "Doctor visit", "Dental care", "Health checkup"],
            "Education": ["Course fee", "Workshop", "Textbooks", "Online course"],
            "Other": ["Personal care", "Gift", "Miscellaneous", "Subscription"],
        }
        return [
            str(self.rng.choice(templates.get(str(category), templates["Other"])))
            for category in categories
        ]

    def generate_tags(self, categories: Iterable[str]) -> list[str]:
        """Attach simple semantic tags to support later grouping."""

        tags = {
            "Rent": "essential; housing",
            "Food & Dining": "essential; food",
            "Transportation": "essential; transport",
            "Entertainment": "leisure",
            "Shopping": "discretionary",
            "Utilities": "essential; bills",
            "Healthcare": "essential; health",
            "Education": "investment",
            "Other": "misc",
        }
        return [tags.get(str(category), "misc") for category in categories]

    def _rent_dates(self) -> list[pd.Timestamp]:
        """Return one in-range date per calendar month."""

        month_starts = pd.date_range(
            self.start_date.to_period("M").start_time,
            self.end_date.to_period("M").start_time,
            freq="MS",
        )
        return [
            max(self.start_date, date_value)
            for date_value in month_starts
            if self.start_date <= date_value <= self.end_date
        ]

    def _add_valid_high_expenses(
        self,
        amounts: list[float],
        categories: list[str],
    ) -> None:
        """Add review-worthy values while keeping them valid transactions."""

        if len(amounts) < 20 or self.outlier_fraction == 0:
            return
        count = min(max(1, int(round(len(amounts) * self.outlier_fraction))), len(amounts))
        indices = self.rng.choice(len(amounts), size=count, replace=False)
        for index in np.atleast_1d(indices):
            position = int(index)
            category = categories[position]
            if category in {"Rent", "Utilities"}:
                continue
            minimum, maximum = CATEGORY_AMOUNT_RANGES.get(
                category, CATEGORY_AMOUNT_RANGES["Other"]
            )
            amounts[position] = round(
                float(self.rng.uniform(maximum * 0.9, maximum * 1.6)), 2
            )

    def generate_data(self) -> pd.DataFrame:
        """Generate a complete raw DataFrame."""

        self._reset_rng()
        if self.num_records == 0:
            self.data = pd.DataFrame(
                columns=[
                    "Expense_ID",
                    "Date",
                    "Category",
                    "Amount",
                    "Description",
                    "Payment_Method",
                    "Tags",
                    "Notes",
                    "Recurring",
                ]
            )
            return self.data.copy()

        rent_dates = self._rent_dates()
        rent_count = min(len(rent_dates), self.num_records)
        variable_count = self.num_records - rent_count
        variable_dates = self.generate_dates(variable_count)
        variable_categories = [
            str(category) for category in self._non_rent_categories(variable_count)
        ]
        variable_amounts = self.generate_amounts(variable_categories, variable_dates)
        self._add_valid_high_expenses(variable_amounts, variable_categories)

        rows: list[dict[str, object]] = []
        for date_value, category, amount in zip(
            variable_dates, variable_categories, variable_amounts
        ):
            rows.append(
                {
                    "Date": date_value,
                    "Category": category,
                    "Amount": amount,
                    "Description": self.generate_descriptions([category])[0],
                    "Payment_Method": str(self.generate_payment_methods(1)[0]),
                    "Tags": self.generate_tags([category])[0],
                    "Notes": "",
                    "Recurring": bool(self.rng.choice([False, True], p=[0.90, 0.10])),
                }
            )

        for date_value in rent_dates[:rent_count]:
            rent_amount = round(float(self.rng.normal(19_500, 250)), 2)
            rows.append(
                {
                    "Date": date_value,
                    "Category": "Rent",
                    "Amount": max(rent_amount, 17_000.0),
                    "Description": "Monthly rent",
                    "Payment_Method": "Bank Transfer",
                    "Tags": "Essential; Housing",
                    "Notes": "Recurring monthly commitment",
                    "Recurring": True,
                }
            )

        data = pd.DataFrame(rows)
        data = data.sort_values("Date", kind="stable").reset_index(drop=True)
        data.insert(0, "Expense_ID", [f"EXP-{index + 1:04d}" for index in range(len(data))])
        data["Date"] = pd.to_datetime(data["Date"])
        self.data = data
        return data.copy()

    def save_data(self, filepath: Path | str = RAW_DATA_PATH) -> Path:
        """Save generated data as CSV and return the destination."""

        if self.data is None:
            self.generate_data()
        destination = Path(filepath)
        destination.parent.mkdir(parents=True, exist_ok=True)
        self.data.to_csv(destination, index=False)
        return destination

    def get_data(self) -> pd.DataFrame:
        """Return a copy of generated data, generating it if required."""

        if self.data is None:
            self.generate_data()
        return self.data.copy()


def generate_and_save_data(
    num_records: int = NUM_RECORDS,
    seed: int = RANDOM_SEED,
    filepath: Path | str = RAW_DATA_PATH,
    start_date: date | str = START_DATE,
    end_date: date | str = END_DATE,
) -> pd.DataFrame:
    """Generate and save data in one call."""

    generator = DataGenerator(
        num_records=num_records,
        seed=seed,
        start_date=start_date,
        end_date=end_date,
    )
    data = generator.generate_data()
    generator.save_data(filepath)
    return data


if __name__ == "__main__":
    generated = generate_and_save_data()
    print(generated.head().to_string(index=False))
    print(f"\nGenerated {len(generated)} rows at {RAW_DATA_PATH}")

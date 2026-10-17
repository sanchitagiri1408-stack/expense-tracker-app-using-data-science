"""Project configuration and shared helpers.

The defaults are intentionally stable so that a recruiter can clone the
repository and reproduce the same synthetic example. All paths are resolved
relative to the project root rather than the current working directory.
"""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs"
REPORTS_DIR = OUTPUT_DIR / "reports"
CHARTS_DIR = OUTPUT_DIR / "charts"

RAW_DATA_PATH = DATA_DIR / "raw_expenses.csv"
CLEANED_DATA_PATH = DATA_DIR / "cleaned_expenses.csv"

# Stable demo window: do not use datetime.now() for generated portfolio data.
NUM_RECORDS = int(os.getenv("EXPENSE_RECORDS", "600"))
START_DATE = date(2024, 1, 1)
END_DATE = date(2024, 6, 30)
DATE_RANGE_DAYS = (END_DATE - START_DATE).days + 1
RANDOM_SEED = int(os.getenv("EXPENSE_SEED", "42"))
CURRENCY = os.getenv("EXPENSE_CURRENCY", "₹") or "₹"

EXPENSE_CATEGORIES = {
    "Rent": 0.06,
    "Food & Dining": 0.25,
    "Transportation": 0.15,
    "Entertainment": 0.10,
    "Shopping": 0.19,
    "Utilities": 0.10,
    "Healthcare": 0.08,
    "Education": 0.05,
    "Other": 0.02,
}

CATEGORY_AMOUNT_RANGES = {
    "Rent": (17_000.0, 22_000.0),
    "Food & Dining": (50.0, 900.0),
    "Transportation": (40.0, 1_200.0),
    "Entertainment": (100.0, 2_000.0),
    "Shopping": (150.0, 5_000.0),
    "Utilities": (500.0, 4_000.0),
    "Healthcare": (200.0, 6_000.0),
    "Education": (500.0, 12_000.0),
    "Other": (50.0, 2_000.0),
}

PAYMENT_METHODS = [
    "Cash",
    "Credit Card",
    "Debit Card",
    "Mobile Payment",
    "Bank Transfer",
]
PAYMENT_METHOD_DISTRIBUTION = {
    "Credit Card": 0.40,
    "Debit Card": 0.25,
    "Mobile Payment": 0.20,
    "Bank Transfer": 0.10,
    "Cash": 0.05,
}

OUTLIER_THRESHOLD = 3.0
HIGH_SPENDING_QUANTILE = 0.75
LOW_SPENDING_QUANTILE = 0.25
OVERSPENDING_RATIO = 1.20

PLOT_STYLE = "seaborn-v0_8-whitegrid"
FIGURE_SIZE = (11, 6)
FIGURE_DPI = 120

CATEGORY_COLORS = {
    "Rent": "#264653",
    "Food & Dining": "#e76f51",
    "Transportation": "#2a9d8f",
    "Entertainment": "#457b9d",
    "Shopping": "#f4a261",
    "Utilities": "#8ab17d",
    "Healthcare": "#e9c46a",
    "Education": "#9b5de5",
    "Other": "#6c757d",
}

DAY_ORDER = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


def ensure_directories(
    data_dir: Path | str = DATA_DIR,
    output_dir: Path | str = OUTPUT_DIR,
) -> dict[str, Path]:
    """Create and return the runtime directories used by the pipeline."""

    data_path = Path(data_dir)
    output_path = Path(output_dir)
    reports_path = output_path / "reports"
    charts_path = output_path / "charts"
    for directory in (data_path, output_path, reports_path, charts_path):
        directory.mkdir(parents=True, exist_ok=True)
    return {
        "data": data_path,
        "output": output_path,
        "reports": reports_path,
        "charts": charts_path,
    }


def format_currency(value: float, currency: str = CURRENCY) -> str:
    """Format a number with the project's currency symbol."""

    return f"{currency}{float(value):,.2f}"


# Create the standard folders on first import. No data is generated here.
ensure_directories()

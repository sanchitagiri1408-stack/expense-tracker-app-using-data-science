"""Command-line entry point for the Expense Tracker App.

Run from the project root:

    python main.py

The command creates reproducible synthetic data, cleans it, runs the analysis,
exports reports, and generates static chart evidence.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.analyzer import ExpenseAnalyzer
from src.config import (
    CURRENCY,
    DATA_DIR,
    END_DATE,
    NUM_RECORDS,
    OUTPUT_DIR,
    RANDOM_SEED,
    START_DATE,
    ensure_directories,
    format_currency,
)
from src.data_cleaner import DataCleaner
from src.data_generator import DataGenerator
from src.visualizer import ExpenseVisualizer


def _json_safe(value: Any) -> Any:
    """Convert common NumPy/Pandas values into JSON-compatible objects."""

    if isinstance(value, pd.DataFrame):
        return [_json_safe(row) for row in value.to_dict(orient="records")]
    if isinstance(value, pd.Series):
        return _json_safe(value.to_dict())
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (pd.Timestamp, pd.Period)):
        return str(value)
    if hasattr(value, "item"):
        try:
            return value.item()
        except (TypeError, ValueError):
            pass
    return value


def _write_json(path: Path, payload: Any) -> None:
    """Write pretty JSON while keeping the report human-readable."""

    path.write_text(json.dumps(_json_safe(payload), indent=2, ensure_ascii=False), encoding="utf-8")


def run_pipeline(
    num_records: int = NUM_RECORDS,
    seed: int = RANDOM_SEED,
    start_date: str | pd.Timestamp = START_DATE,
    end_date: str | pd.Timestamp = END_DATE,
    currency: str = CURRENCY,
    data_dir: Path | str = DATA_DIR,
    output_dir: Path | str = OUTPUT_DIR,
    generate_charts: bool = True,
) -> dict[str, Any]:
    """Run all project stages and return paths, KPIs, and insights.

    The arguments make the pipeline easy to test without touching the
    repository's default data or output directories.
    """

    directories = ensure_directories(data_dir=data_dir, output_dir=output_dir)
    raw_path = directories["data"] / "raw_expenses.csv"
    cleaned_path = directories["data"] / "cleaned_expenses.csv"

    generator = DataGenerator(
        num_records=num_records,
        seed=seed,
        start_date=start_date,
        end_date=end_date,
    )
    raw_data = generator.generate_data()
    generator.save_data(raw_path)

    cleaner = DataCleaner(data=raw_data, as_of=pd.Timestamp(end_date))
    cleaned_data = cleaner.clean_data()
    cleaner.save_cleaned_data(cleaned_path)

    analyzer = ExpenseAnalyzer(data=cleaned_data, currency=currency)
    analyzer.analyze_all()

    reports_dir = directories["reports"]
    for table_name, table in analyzer.tables.items():
        if table_name == "correlation_matrix":
            table.to_csv(reports_dir / "correlation_matrix.csv")
        elif isinstance(table, pd.DataFrame):
            table.to_csv(reports_dir / f"{table_name}.csv", index=False)
    _write_json(reports_dir / "kpis.json", analyzer.get_statistics())
    _write_json(reports_dir / "cleaning_report.json", cleaner.get_cleaning_report())
    (reports_dir / "insights.txt").write_text(
        analyzer.generate_summary_report(), encoding="utf-8"
    )

    chart_paths: dict[str, Path] = {}
    if generate_charts and not cleaned_data.empty:
        chart_paths = ExpenseVisualizer(
            cleaned_data,
            output_dir=directories["charts"],
            currency=currency,
        ).visualize_all()

    return {
        "raw_path": raw_path,
        "cleaned_path": cleaned_path,
        "reports_dir": reports_dir,
        "charts_dir": directories["charts"],
        "raw_rows": len(raw_data),
        "cleaned_rows": len(cleaned_data),
        "kpis": analyzer.get_statistics(),
        "insights": analyzer.get_insights(),
        "cleaning_report": cleaner.get_cleaning_report(),
        "chart_paths": chart_paths,
    }


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""

    parser = argparse.ArgumentParser(description="Run the synthetic expense analytics pipeline.")
    parser.add_argument("--records", type=int, default=NUM_RECORDS, help="Number of synthetic records to create.")
    parser.add_argument("--seed", type=int, default=RANDOM_SEED, help="Random seed for reproducibility.")
    parser.add_argument("--start-date", default=str(START_DATE), help="Inclusive start date in YYYY-MM-DD format.")
    parser.add_argument("--end-date", default=str(END_DATE), help="Inclusive end date in YYYY-MM-DD format.")
    parser.add_argument("--currency", default=CURRENCY, help="Currency symbol used in reports and charts.")
    parser.add_argument("--skip-charts", action="store_true", help="Run data and reports without PNG generation.")
    return parser


def main() -> None:
    """Parse arguments, run the pipeline, and print a useful summary."""

    args = build_parser().parse_args()
    if args.records < 0:
        raise SystemExit("--records must be zero or greater")

    result = run_pipeline(
        num_records=args.records,
        seed=args.seed,
        start_date=args.start_date,
        end_date=args.end_date,
        currency=args.currency,
        generate_charts=not args.skip_charts,
    )
    kpis = result["kpis"]

    print("\n" + "=" * 68)
    print("EXPENSE TRACKER APP — DATA SCIENCE PIPELINE")
    print("=" * 68)
    print("Synthetic data only | Portfolio/demo project | Not financial advice")
    print(f"\nRows generated: {result['raw_rows']:,}")
    print(f"Rows after cleaning: {result['cleaned_rows']:,}")
    print(f"Total spending: {format_currency(kpis['total_expenses'], args.currency)}")
    print(f"Average transaction: {format_currency(kpis['average_transaction'], args.currency)}")
    print(f"Average daily spending: {format_currency(kpis['average_daily_spending'], args.currency)}")
    print(f"Flagged transactions for review: {kpis.get('anomalies', {}).get('flagged_count', 0)}")
    print("\nTop insights:")
    for message in result["insights"][:5]:
        print(f"  • {message}")
    print("\nFiles written:")
    print(f"  • {result['raw_path']}")
    print(f"  • {result['cleaned_path']}")
    print(f"  • {result['reports_dir']}")
    print(f"  • {len(result['chart_paths'])} charts in {result['charts_dir']}")
    print("=" * 68 + "\n")


if __name__ == "__main__":
    main()

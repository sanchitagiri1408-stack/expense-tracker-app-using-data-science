# Execution, GitHub Upload, and Finishing Checklist

Use this page after cloning or downloading the project. The commands assume
you are in the repository root: `Expense-Tracker-App/`.

## 1. Install and verify

### Windows PowerShell

```powershell
py -3.10 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip check
```

If PowerShell blocks activation, run this only for the current terminal:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip check
```

## 2. Execute the project

Run the main data-science workflow:

```bash
python main.py
```

It will:

1. Generate 600 reproducible synthetic transactions.
2. Save `data/raw_expenses.csv`.
3. Clean and enrich the data.
4. Save `data/cleaned_expenses.csv`.
5. Create analysis tables, JSON KPIs, and insights in `outputs/reports/`.
6. Create eight PNG charts in `outputs/charts/`.

Useful optional commands:

```bash
# Smaller run while experimenting
python main.py --records 100 --seed 7

# Use a different reproducible date window
python main.py --start-date 2024-01-01 --end-date 2024-12-31 --seed 42

# Run the pipeline without chart generation
python main.py --skip-charts
```

Run the tests:

```bash
python -m pytest -q
```

Open the interactive dashboard:

```bash
streamlit run app.py
```

If the `streamlit` command is not found:

```bash
python -m streamlit run app.py
```

Open the printed local URL, normally `http://localhost:8501`. Test the date,
category, and payment-method filters, then download the filtered CSV.

## 3. Review the generated evidence

Before publishing, inspect:

```text
data/raw_expenses.csv
data/cleaned_expenses.csv
outputs/reports/kpis.json
outputs/reports/cleaning_report.json
outputs/reports/insights.txt
outputs/reports/category_summary.csv
outputs/reports/monthly_summary.csv
outputs/charts/*.png
```

Use the actual values from the current run in screenshots and interview
answers. Every result must be labeled synthetic.

## 4. Capture portfolio proof

Save reviewed screenshots under `images/` with these names:

1. `01_environment.png` — Python version and installation/check success.
2. `02_project_structure.png` — the repository tree.
3. `03_raw_data_preview.png` — first rows, columns, and data types.
4. `04_cleaning_evidence.png` — cleaning report and outlier policy.
5. `05_cleaned_data_preview.png` — derived columns and valid values.
6. `06_cli_run.png` — completed `python main.py` output.
7. `07_charts.png` — category chart, monthly trend, and heatmap.
8. `08_dashboard_overview.png` — dashboard KPIs and charts.
9. `09_dashboard_filter.png` — a filter interaction with changed results.
10. `10_test_result.png` — actual `python -m pytest -q` output.
11. `11_github_repository.png` — GitHub tree, README, topics, and commits.

Do not include personal financial data, API keys, tokens, local credentials, or
private paths in screenshots.

## 5. Create and upload the GitHub repository

Recommended repository name:

```text
expense-tracker-app-using-data-science
```

Recommended description:

```text
Reproducible synthetic expense analytics pipeline with Pandas, visualization, tests, and a Streamlit dashboard.
```

Create a **public empty repository** on GitHub. Do not add a second README,
`.gitignore`, or license if they already exist locally. Then run:

```bash
git init
git branch -M main
git add .
git status
git diff --cached --stat
git commit -m "feat: build synthetic expense analytics application"
git remote add origin https://github.com/<YOUR_USERNAME>/expense-tracker-app-using-data-science.git
git remote -v
git push -u origin main
```

If the remote already contains a README or another initial commit, stop and
resolve that history deliberately; do not overwrite it blindly.

### Suggested professional commit history

If you want a learning-friendly history instead of one large commit:

```bash
git add requirements.txt .gitignore src main.py
git commit -m "feat: add reproducible expense data pipeline"

git add tests
git commit -m "test: cover cleaning analysis and visualization"

git add app.py outputs/charts outputs/reports
git commit -m "feat: add dashboard and analysis evidence"

git add README.md docs notebooks PROJECT_GUIDE.md
git commit -m "docs: publish portfolio guide and interview preparation"

git push -u origin main
```

Add these GitHub topics:

```text
python, data-science, data-analysis, pandas, numpy, matplotlib, seaborn,
plotly, streamlit, expense-tracker, portfolio-project, synthetic-data
```

## 6. Final finishing review

Run the following before sharing the repository URL:

```bash
python -m pip check
python -m pytest -q
python main.py
git status
git diff --stat
```

Confirm:

- The README commands work from a fresh environment.
- The dashboard starts and filters change the displayed data.
- The report and chart files are generated by the current code.
- The raw and cleaned CSVs are clearly synthetic.
- The `.gitignore` excludes environments, caches, secrets, and local CSVs.
- No tests or results are claimed unless the command was actually run.
- The repository contains no real financial records or credentials.
- Interview answers mention limitations and do not present synthetic numbers as facts.

## 7. Placement-ready explanation

Use this order in a demo:

1. State the business problem: expense rows are difficult to review manually.
2. Explain the synthetic-data decision and reproducibility boundary.
3. Show the raw-to-cleaned pipeline and data-quality report.
4. Show one category chart and one monthly chart tied to a question.
5. Demonstrate one dashboard filter.
6. Explain the anomaly flag as a review signal, not fraud detection.
7. Mention tests, limitations, and the next production improvement.

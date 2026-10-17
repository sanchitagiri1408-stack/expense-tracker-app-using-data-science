# Expense Tracker App — Project Plan

This plan defines the nine implementation phases and a five-day execution/proof schedule for a placement-ready portfolio project. The data is synthetic and explicitly for demonstration. Do not report generated numbers as real-world facts or financial advice.

## Definition of done

- [ ] A Python 3.10+ environment installs from `requirements.txt`.
- [ ] The project follows the selected **Option B** contract: modular Python pipeline plus Streamlit dashboard.
- [ ] `python main.py` is the documented CLI entrypoint.
- [ ] `python -m pytest` is the documented test command and its actual result is recorded.
- [ ] `streamlit run app.py` is the documented dashboard command.
- [ ] Raw and cleaned synthetic CSVs are explainable and reproducible.
- [ ] Charts, reports, and screenshots are tied to an actual run.
- [ ] README, interview preparation, limitations, and future work are complete.
- [ ] No secrets, personal financial exports, or fabricated notebook outputs are committed.

## Nine implementation phases

| Phase | What to do | Why it matters | Expected output | Common mistakes |
| --- | --- | --- | --- | --- |
| 1. Project setup | Create folders, venv, requirements, ignore rules, CLI/dashboard/test contracts, and Git history. | Makes setup repeatable and reviewable. | Installable root project and clean status. | Global Python, hand-installed packages, missing `.gitignore`. |
| 2. Synthetic data | Generate controlled dates, categories, amounts, descriptions, payment methods, tags, notes, recurring flags, and a few unusual amounts. | Safe public data with controlled edge cases. | `data/raw_expenses.csv`, schema note, generator evidence. | Calling synthetic values real; no seed; no variation. |
| 3. Cleaning | Profile nulls/duplicates, convert types, validate amounts/dates, flag outliers, standardize text, add date fields. | Makes quality decisions explicit before analysis. | `data/cleaned_expenses.csv`, cleaning report, before/after counts. | Silent row drops, undocumented imputation, removing all outliers. |
| 4. EDA | Inspect shape, dtypes, distributions, categories, percentiles, missingness, and unusual rows. | Finds patterns and questions before KPI claims. | Notebook tables, distribution charts, investigation questions. | Treating correlation as causation; trusting only averages. |
| 5. Feature engineering | Add month, week, weekday, day-of-month, weekend, recurring, and explainable spending flags. | Enables consistent time and segment comparisons. | Enriched data plus field definitions. | Leakage, redundant fields, magic thresholds. |
| 6. Analysis | Calculate totals, count, mean/median, min/max, category/payment shares, temporal trends, recurring summaries, and anomaly details. | Turns rows into decision-ready measures. | Analysis tables and insight candidates. | Missing denominator/time window; count confused with spend. |
| 7. Visualization | Produce labeled static charts and Streamlit/Plotly views with readable filters and units. | Communicates evidence to technical and non-technical viewers. | `outputs/charts/*.png`, dashboard, screenshots. | Decorative charts, unreadable labels, hidden disclaimer. |
| 8. Insights | Write cautious findings, quantify observed patterns, state uncertainty, and suggest the next question. | Shows business interpretation, not just coding. | Report/README results section linked to artifacts. | Financial advice, unsupported generalization, vague recommendations. |
| 9. GitHub and documentation | Run checks, review files, write README/docs, select screenshots, commit clearly, add topics, and push. | Makes the work easy to reproduce and discover. | Public repository with proof and honest limitations. | Secrets, broken notebooks, vague commits, unrun checks claimed as passed. |

## Five-day execution and proof checklist

### Day 1 — Reproducible foundation

**Build**

- [ ] Confirm Python 3.10+ and Git.
- [ ] Create `.venv` and install `requirements.txt`.
- [ ] Review the root structure and entrypoint contract.
- [ ] Read `.gitignore` and confirm it does not hide source/docs or the whole `outputs/` directory.
- [ ] Run `python -m pip check`.

**Proof**

- [ ] Capture Python version and installation success in `images/01_environment.png`.
- [ ] Capture the root tree in `images/02_project_structure.png`.
- [ ] Record the actual environment date and platform.

**Checkpoint**

```bash
python --version
python -m pip install -r requirements.txt
python -m pip check
git status
```

Suggested commit: `chore: make project reproducible`.

### Day 2 — Synthetic data and schema

**Build**

- [ ] Run the generator through the supported project flow.
- [ ] Inspect raw columns, row count, dtypes, categories, payment methods, and amount range.
- [ ] Write a small schema/data dictionary note.
- [ ] Confirm the synthetic label is visible in documentation or dashboard.

**Proof**

- [ ] Capture first rows and dtypes in `images/03_raw_data_preview.png`.
- [ ] Capture the generator terminal output.
- [ ] Record seed, configured record count, and relative date-window behavior.

**Checkpoint**

```bash
python main.py
python -c "import pandas as pd; df = pd.read_csv('data/raw_expenses.csv'); print(df.shape); print(df.dtypes)"
```

Suggested commit: `feat: add reproducible synthetic expense generator`.

### Day 3 — Cleaning and EDA

**Build**

- [ ] Run `notebooks/01_data_generation.ipynb` from the project root.
- [ ] Run `notebooks/02_data_cleaning.ipynb` from the project root.
- [ ] Check missing values, exact duplicates, types, positive amounts, date bounds, and outlier flags.
- [ ] Compare raw and cleaned rows and save `data/cleaned_expenses.csv`.

**Proof**

- [ ] Capture the cleaning summary in `images/04_cleaning_evidence.png`.
- [ ] Capture cleaned rows and derived columns in `images/05_cleaned_data_preview.png`.
- [ ] Save the actual notebook run date separately; do not commit fabricated cell outputs.

**Checkpoint**

```bash
jupyter notebook notebooks/01_data_generation.ipynb
jupyter notebook notebooks/02_data_cleaning.ipynb
```

Suggested commit: `feat: add cleaning and EDA walkthrough`.

### Day 4 — Analysis, charts, and dashboard

**Build**

- [ ] Run the CLI contract and inspect the generated outputs.
- [ ] Review category, monthly, payment, distribution, heatmap, and day-of-week charts.
- [ ] Open Streamlit and test at least one meaningful filter.
- [ ] Ensure the dashboard explains synthetic data and units.

**Proof**

- [ ] Capture `python main.py` in `images/06_cli_run.png`.
- [ ] Capture selected chart evidence in `images/07_chart_evidence.png`.
- [ ] Capture dashboard overview/filter states in `images/08_dashboard_overview.png` and `images/09_dashboard_filter.png`.

**Checkpoint**

```bash
python main.py
streamlit run app.py
```

Suggested commit: `feat: add analysis dashboard and evidence`.

### Day 5 — Tests, publication, and rehearsal

**Build**

- [ ] Run the complete test command and save its actual result.
- [ ] Review README setup, run commands, outputs, limitations, and troubleshooting.
- [ ] Review docs/interview answers against actual implementation.
- [ ] Remove secrets, personal data, stale screenshots, and unreviewed outputs.
- [ ] Create the GitHub repository, add topics, push, and view the rendered README.

**Proof**

- [ ] Capture `python -m pytest` in `images/10_test_result.png`.
- [ ] Capture GitHub tree, README, topics, and commits in `images/11_github_repository.png`.
- [ ] Rehearse a two-minute explanation and a role-specific answer.

**Checkpoint**

```bash
python -m pytest
git status
git diff --stat
git log --oneline -5
```

Suggested commit: `docs: publish portfolio evidence`.

## Evidence-to-claim map

| Portfolio claim | Evidence required |
| --- | --- |
| “The project is reproducible.” | Setup screenshot, requirements file, exact commands, actual run date. |
| “The data was cleaned.” | Before/after rows, missing/duplicate checks, type validation, cleaning report. |
| “The dashboard is interactive.” | Streamlit screenshot plus a filter interaction and changed result. |
| “The project detects anomalies.” | Outlier rule, flagged-field screenshot, and limitation that it is not fraud detection. |
| “The tests pass.” | Actual `python -m pytest` output from the current checkout. |
| “The analysis found a real trend.” | Do not make this claim from synthetic data; say “the generated sample shows…” and include the exact run evidence. |

## Release review

Before publishing, check:

- [ ] All README commands are copied exactly: `python main.py`, `python -m pytest`, `streamlit run app.py`.
- [ ] `requirements.txt` contains only the needed, compatible analysis, dashboard, notebook, and test dependencies.
- [ ] `outputs/` is not ignored wholesale; selected proof charts can be tracked.
- [ ] Generated data is labeled synthetic and personal data is absent.
- [ ] Notebook cells are aligned with the current `src` APIs and outputs are not fabricated.
- [ ] Limitations and future ML ideas are included.
- [ ] Every reported check was actually run and recorded.

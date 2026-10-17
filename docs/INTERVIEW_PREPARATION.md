# Interview Preparation

This guide turns the Expense Tracker App into a concise, evidence-based interview story. Replace bracketed notes with values from an actual run. Never present synthetic numbers as real-world facts, and describe the project as a portfolio/demo tool rather than financial advice.

## Thirty-second answer

> I built an Expense Tracker App using Python data-science tools and Streamlit. It generates labeled synthetic expense records, cleans and validates them, calculates category and time-based KPIs, flags unusual amounts, creates charts, and exposes the workflow through a CLI and dashboard. I chose synthetic data because financial records are sensitive and I wanted a reproducible project that recruiters can run. The project demonstrates the complete path from raw data to a decision-friendly visual output, while clearly documenting that the results are illustrative rather than financial advice.

## Role-specific positioning

### Data Analyst

**Answer:**

> I approached the project as a data-quality and insight workflow. I profiled the schema, checked missing values and duplicates, converted dates and amounts, validated positive values, flagged outliers, and added time features. I then used descriptive statistics, category/payment aggregations, monthly trends, percentiles, and charts to answer where and when spending is concentrated. My emphasis is traceability: every KPI should have a clear definition, denominator, time window, and source column.

**Likely follow-ups:**

- **How did you clean it?** I used a documented sequence: missing-value report, exact-duplicate removal, date/amount conversion, amount/date validation, configurable outlier flagging, text standardization, and derived date fields. I avoid silently dropping unusual rows.
- **Which visualizations did you choose?** Category bars or a pie chart show composition, a monthly line shows change over time, a histogram shows skew and the mean/median relationship, a heatmap shows time patterns, and payment-method bars compare channels. Each visual answers a question rather than decorating the dashboard.
- **How did you validate the analysis?** I compare row counts before and after cleaning, inspect dtypes and null counts, check positive amounts and valid dates, compare totals by category, and run automated tests for important boundaries.

### Business Analyst

**Answer:**

> I framed the project around a business question: how can a user or manager see expense concentration and unusual activity without manually aggregating a ledger? I translated that question into requirements—category totals, time trends, recurring-spend views, payment-method comparison, anomaly review, and exportable evidence. I kept the dashboard focused on decisions and documented assumptions so a stakeholder can understand what the numbers mean and what they do not mean.

**Likely follow-ups:**

- **What is the stakeholder value?** It shortens the path from transaction rows to a repeatable review. A manager can see the largest categories, trend direction, and items that need investigation instead of relying on a spreadsheet inspection.
- **How would you prioritize improvements?** I would first add a validated input schema and budget/period comparisons, then permissions and an audit trail, and only afterward add prediction. This protects trust before adding complexity.
- **How do you communicate limitations?** I state that the data is synthetic, the default date window is fixed only for reproducibility, anomaly flags are review signals rather than fraud findings, and no financial decision should be made from the demo.

### Financial Analyst

**Answer:**

> I use the project to demonstrate disciplined expense reporting, not to give financial advice. I selected total spend, transaction count, mean and median transaction value, category/payment shares, recurring versus non-recurring totals, and period trends because they describe scale, composition, activity, and direction. I would ask for a real source system, accounting definitions, currency, period close rules, and reconciliation controls before using a similar workflow for actual financial reporting.

**Likely follow-ups:**

- **Why are mean and median both useful?** Expense amounts can be right-skewed. The mean reflects total spend per transaction, while the median shows a more typical transaction. A large gap is a prompt to inspect distribution and outliers.
- **What does an anomaly mean?** The current category-relative z-score/IQR rule identifies an amount that is unusual relative to this synthetic sample. It does not identify fraud, error, affordability, or materiality without business context.
- **What controls would production need?** Source reconciliation, period and currency controls, user permissions, immutable audit history, validation rules, exception review, backups, and clear ownership of financial definitions.

## Strong technical answers

### Why synthetic data instead of real financial data?

Real expenses may contain personally identifiable or commercially sensitive information, and a public portfolio should not expose them. Synthetic data lets me control the schema, volume, categories, date range, missingness/outlier scenarios, and random seed. It also makes the project reproducible for a recruiter. The trade-off is that the patterns are designed, not evidence about real households or businesses, so I label every result as synthetic.

### What is the cleaning pipeline?

1. Inspect shape, columns, null counts, duplicates, and data types.
2. Fill only documented fields when missing values occur; preserve a cleaning report.
3. Remove exact duplicate records.
4. Parse `Date`, coerce `Amount` to numeric, and validate positive amounts and reasonable dates.
5. Detect unusual amounts with a category-relative z-score/IQR rule and keep an `Is_Outlier` flag by default.
6. Standardize text and add `DayOfWeek`, `Month`, `Week`, `DayOfMonth`, and `IsWeekend`.
7. Compare before/after row counts and save `data/cleaned_expenses.csv`.

The purpose is not to make the data look perfect; it is to make decisions explicit and reviewable.

### How did you choose KPIs?

- **Total expenses:** overall scale for the selected data window.
- **Transaction count:** activity level; it is not the same as total spend.
- **Mean and median transaction:** typical value and sensitivity to skew.
- **Minimum and maximum:** range and review boundaries.
- **Category/payment totals and percentages:** composition and channel mix.
- **Daily/weekly/monthly totals:** direction and concentration over time.
- **Recurring summary:** repeatable commitments versus one-off activity.

I would add budget variance only after a budget definition and period basis were agreed.

### How did you choose visualizations?

I map each business question to one chart: bars for category comparison, a pie only for a small number of composition categories, a line for monthly direction, a histogram for distribution, a heatmap for day/week patterns, and paired payment-method charts for amount versus count. I label currency units, avoid implying causation, and keep the synthetic-data disclaimer visible.

### How does anomaly detection work?

The cleaner calculates category-relative z-scores and an IQR upper bound, then flags unusual values. The analyzer reports flagged rows and the most/least expensive transactions. I would compare this baseline with median absolute deviation and time-aware rules in production. No detector can decide whether a transaction is fraudulent without context and investigation.

### What checks prove the pipeline works?

I run `python -m pytest`, inspect the actual terminal result, and capture the command and environment. Useful tests cover generated columns, positive amounts, date parsing, duplicate handling, empty input behavior, outlier flag type, and KPI calculations on a small hand-built DataFrame. I also smoke-test `python main.py`, `streamlit run app.py`, and the two notebooks when those entrypoints are present.

## Limitations and future ML ideas

### Current limitations

- Data is synthetic, hand-designed, and not statistically representative.
- The default date window moves with the run date, so screenshots need a capture date.
- The category-relative z-score/IQR flag is a baseline review rule, not fraud detection.
- There is no live bank connector, authentication, database audit trail, currency conversion, or accounting/tax treatment.
- The current analysis is descriptive, not predictive, and is not financial advice.

### Responsible future ML ideas

1. **Anomaly ranking:** engineer amount, category, weekday, recurring, and rolling-history features; compare Isolation Forest or robust statistical baselines; review false positives with a human.
2. **Cash-flow forecasting:** aggregate by day/week, use a time-based train/validation split, compare seasonal-naive, moving-average, and ML baselines, and report prediction intervals.
3. **Category classification:** train on reviewed user-labeled descriptions only; measure precision/recall by category and allow manual correction.
4. **Subscription detection:** use recurring cadence and merchant-like descriptions, then ask the user to confirm instead of silently labeling a payment.
5. **Budget-risk alerts:** predict period-end variance only after a user-defined budget, stable history, and a clear threshold exist.

For every ML addition I would document the target, leakage risks, baseline, evaluation split, metrics, uncertainty, and human override. A more complex model is not automatically a better financial decision tool.

## One-minute STAR story

- **Situation:** A raw expense table is hard to review and real financial records are not safe to publish.
- **Task:** Build a reproducible portfolio example that demonstrates the full analytics workflow.
- **Action:** I generated labeled synthetic data, created a cleaning pipeline, designed interpretable KPIs, added anomaly flags and charts, exposed the result through CLI/Streamlit contracts, and documented setup and limitations.
- **Result:** A recruiter can reproduce the workflow, inspect the data-quality decisions, and see evidence from the dashboard. The result is explicitly illustrative and not financial advice.

## Interview discipline checklist

Before an interview, confirm that you can show:

- The exact command you ran and the date of the run.
- A raw-data screenshot and cleaned-data screenshot.
- One KPI table and one chart that answer a clear question.
- The outlier rule and why it is only a review signal.
- The synthetic-data rationale and its limitations.
- One improvement that increases trust before one that merely adds complexity.
- The actual `python -m pytest` result; never claim tests passed without running them.

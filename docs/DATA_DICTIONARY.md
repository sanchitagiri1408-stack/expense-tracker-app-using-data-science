# Expense Data Dictionary

The default files are generated synthetic data. Values are safe for a public
portfolio and must not be described as real financial records.

## Raw columns

| Column | Type | Meaning | Example |
| --- | --- | --- | --- |
| `Expense_ID` | string | Reproducible transaction identifier | `EXP-0001` |
| `Date` | date | Date of the expense | `2024-01-15` |
| `Category` | string | Spending group | `Food & Dining` |
| `Amount` | float | Positive expense amount in the configured currency | `599.95` |
| `Description` | string | Human-readable transaction label | `Groceries` |
| `Payment_Method` | string | Payment channel | `Mobile Payment` |
| `Tags` | string | Simple semantic tags | `essential; food` |
| `Notes` | string | Optional context | `Recurring monthly commitment` |
| `Recurring` | boolean | Whether the generator treats the transaction as recurring | `True` |

## Cleaned and engineered columns

| Column | Meaning |
| --- | --- |
| `Outlier_Z_Score` | Category-relative standardized amount used for review. |
| `Is_Outlier` | `True` when the category-relative z-score or IQR rule flags the row. |
| `YearMonth` | Calendar month key such as `2024-01`. |
| `Month` | Short month label such as `Jan`. |
| `Week` | ISO week number. |
| `DayOfMonth` | Calendar day number. |
| `DayOfWeek` | Day name such as `Saturday`. |
| `DayOfWeekNum` | Monday=0 through Sunday=6. |
| `IsWeekend` | Whether the date is Saturday or Sunday. |
| `SpendingLevel` | `Low`, `Medium`, or `High` using sample quartiles. |
| `CategoryAverage` | Mean transaction amount within the row's category. |
| `CategoryRatio` | Amount divided by that category average. |
| `CumulativeMonthlySpend` | Running total within the row's calendar month. |
| `Is_High_Spending` | Whether the amount is at or above the overall 75th percentile. |
| `Is_Category_Anomaly` | Whether `CategoryRatio` is at least 1.5. |

## Analysis definitions

- **Total spending:** sum of `Amount` for the selected rows and date window.
- **Average transaction:** mean of `Amount`; it may be affected by large values.
- **Median transaction:** middle transaction value; useful for skewed distributions.
- **Category percentage:** category total divided by total spending.
- **Weekend spending percentage:** weekend amount divided by total amount.
- **Educational overspending baseline:** a month is flagged when its total is
  greater than 1.2 times the mean monthly total. This is not a user budget.
- **Anomaly:** a statistical review flag, not a fraud, error, affordability, or
  materiality conclusion.

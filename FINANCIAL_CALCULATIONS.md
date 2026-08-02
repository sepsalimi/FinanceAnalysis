# Financial Calculations

All formulas are implemented in `backend/app/services/calculations.py` and related analytics services. UI components must not invent totals.

## Signed amount convention

- **Positive** = money entering an account (inflow)
- **Negative** = money leaving an account (outflow)

Canonical events store `confirmed_amount` using this convention in the event’s `confirmed_currency` (usually household default).

## Income

Sum of confirmed events where:

- `event_type` in income-like types (employment, interest, etc. mapped via category or type)
- `analytics_inclusion_status = included`
- `overall_assessment_status` indicates assessed/confirmed
- Not transfer / settlement / reimbursement-as-income

Pending income is tracked separately when the user opts in.

## Expenses

Sum of absolute outflows for expense-classified confirmed events, excluding:

- Transfers between owned accounts
- Credit card payments (transfer)
- Splitwise settlements counted as transfers
- Events excluded from analytics
- Events already counted via another primary payment evidence relationship

## Net cash flow

```text
net_cash_flow = income_total + expense_total
```

Where `expense_total` is signed (negative). Equivalent: income − |expenses|.

## Savings rate

```text
savings_rate = net_cash_flow / income_total   if income_total > 0
savings_rate = null                           if income_total == 0
```

## Annualized recurring amounts

| Frequency | Multiplier |
|-----------|------------|
| weekly | 52 |
| biweekly | 26 |
| semimonthly | 24 |
| monthly | 12 |
| every_two_months | 6 |
| quarterly | 4 |
| semiannually | 2 |
| annually | 1 |
| custom | days_in_year / interval_days |

## Account balances

Prefer reconciled balances from account records; optionally derive from opening balance + signed events when reconciliation is enabled.

## Net worth

```text
net_worth = sum(assets.current_value where include_in_net_worth)
          + sum(financial_accounts balances where include_in_net_worth and asset-like)
          - sum(debts.current_balance)
          - sum(liability account balances)
```

Credit card / loan account balances are liabilities.

## Category totals

Group confirmed included expenses by category/subcategory for a date range. Pending amounts returned as sibling fields, never silently mixed.

## Member allocations

Household totals count each event once. Member views use `financial_event_allocations` net/owed/paid fields.

## Household economic share

For Splitwise-linked events:

```text
household_economic_share = sum of confirmed allocations for household members
```

External shares become receivables/payables and are not household spending.

## Budget variance

```text
variance = budget_amount - actual_confirmed_spend
```

## Planned vs actual

Match planned items to linked events when present; otherwise compare period sums by category.

## Trends

Month-over-month:

```text
pct_change = (current - previous) / |previous|   if previous != 0
```

## Confirmed vs pending

Every analytics endpoint returns:

- `confirmed_total`
- `pending_total`
- `pending_count`
- `assessment_completion_pct`
- `pending_included` (bool reflecting request option)

## Receivables / payables

From Splitwise participant allocations and unmatched reimbursements:

- Receivable: external owes household
- Payable: household owes external

Settlements reduce these balances and are not income/expense.

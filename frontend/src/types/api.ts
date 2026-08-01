export type ApiDecimal = string | { toString(): string };

export type ApiCollection<T> = {
  items?: T[];
  results?: T[];
  data?: T[];
  total?: number;
};

export type RecordLike = Record<string, unknown>;

export type HouseholdSummary = {
  household_name?: string;
  currency?: string;
  timezone?: string;
  net_worth?: ApiDecimal | null;
  cash_balance?: ApiDecimal | null;
  monthly_income?: ApiDecimal | null;
  monthly_expenses?: ApiDecimal | null;
  savings_rate?: ApiDecimal | null;
  pending_review_count?: number | null;
  data_quality_score?: ApiDecimal | null;
};

export type CashFlowPoint = {
  period: string;
  income?: ApiDecimal | null;
  expenses?: ApiDecimal | null;
  net?: ApiDecimal | null;
};

import { format, parseISO } from "date-fns";

type DecimalLike = string | { toString(): string } | null | undefined;

export function decimalToNumber(value: DecimalLike): number | null {
  if (value === null || value === undefined) {
    return null;
  }

  const parsed = Number(value.toString());
  return Number.isFinite(parsed) ? parsed : null;
}

export function formatMoney(
  amount: DecimalLike,
  currency = "USD",
  options: Intl.NumberFormatOptions = {}
) {
  const value = decimalToNumber(amount);

  if (value === null) {
    return "—";
  }

  return new Intl.NumberFormat("en", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
    ...options
  }).format(value);
}

export function formatPercent(value: DecimalLike) {
  const numericValue = decimalToNumber(value);

  if (numericValue === null) {
    return "—";
  }

  return new Intl.NumberFormat("en", {
    style: "percent",
    maximumFractionDigits: 1
  }).format(numericValue);
}

export function formatApiDate(value: string | null | undefined) {
  if (!value) {
    return "—";
  }

  try {
    return format(parseISO(value), "MMM d, yyyy");
  } catch {
    return value;
  }
}

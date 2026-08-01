/**
 * Locale helpers for onboarding defaults.
 * Suggested currency comes from the browser locale and is never hardcoded as the only option.
 */

export function suggestedCurrencyFromLocale(locale?: string): string {
  const resolved =
    locale ||
    (typeof navigator !== "undefined" ? navigator.language : undefined) ||
    "en-US";

  try {
    const currency = new Intl.NumberFormat(resolved, {
      style: "currency",
      currency: "USD"
    })
      .resolvedOptions()
      .currency;

    // Prefer region-aware currency when the locale maps cleanly.
    const regionCurrency = new Intl.NumberFormat(resolved, {
      style: "currency",
      currencyDisplay: "code",
      currency: guessCurrencyCode(resolved)
    })
      .resolvedOptions()
      .currency;

    return (regionCurrency || currency || "USD").toUpperCase();
  } catch {
    return guessCurrencyCode(resolved);
  }
}

function guessCurrencyCode(locale: string): string {
  const normalized = locale.toLowerCase();
  if (normalized.includes("ca")) return "CAD";
  if (normalized.includes("gb")) return "GBP";
  if (normalized.includes("au")) return "AUD";
  if (normalized.includes("eu") || normalized.endsWith("-de") || normalized.endsWith("-fr")) {
    return "EUR";
  }
  if (normalized.includes("jp")) return "JPY";
  return "USD";
}

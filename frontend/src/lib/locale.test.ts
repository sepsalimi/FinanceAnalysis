import { describe, expect, it } from "vitest";

import { suggestedCurrencyFromLocale } from "./locale";

describe("suggestedCurrencyFromLocale", () => {
  it("suggests CAD for Canadian locales", () => {
    expect(suggestedCurrencyFromLocale("en-CA")).toBe("CAD");
  });

  it("does not hardcode a single currency for all locales", () => {
    expect(suggestedCurrencyFromLocale("en-US")).toBe("USD");
    expect(suggestedCurrencyFromLocale("en-GB")).toBe("GBP");
  });
});

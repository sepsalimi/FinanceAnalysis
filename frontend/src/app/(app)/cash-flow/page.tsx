import { SectionPage } from "@/components/data/section-page";

export default function CashFlowPage() {
  return (
    <SectionPage
      title="Cash Flow"
      description="Understand income, expenses, and net movement by API-provided period."
      endpoint="/cash-flow"
      preferredColumns={["period", "income", "expenses", "net", "currency"]}
    />
  );
}

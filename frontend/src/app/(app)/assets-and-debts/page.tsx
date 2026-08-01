import { SectionPage } from "@/components/data/section-page";

export default function AssetsAndDebtsPage() {
  return (
    <SectionPage
      title="Assets and Debts"
      description="See assets, liabilities, ownership, valuation dates, and debt details from the API."
      endpoint="/assets-and-debts"
      preferredColumns={[
        "name",
        "type",
        "current_value",
        "balance",
        "currency",
        "owner",
        "updated_at"
      ]}
    />
  );
}

import { SectionPage } from "@/components/data/section-page";

export default function TransactionsPage() {
  return (
    <SectionPage
      title="Transactions"
      description="Search and inspect imported transactions with categories, matches, transfer links, and review status from the API."
      endpoint="/transactions"
      preferredColumns={[
        "date",
        "description",
        "merchant",
        "amount",
        "currency",
        "category",
        "account",
        "status"
      ]}
    />
  );
}

import { SectionPage } from "@/components/data/section-page";

export default function CategoriesPage() {
  return (
    <SectionPage
      title="Categories"
      description="Manage transaction categories, hierarchy, budgeting metadata, and review coverage."
      endpoint="/categories"
      preferredColumns={[
        "name",
        "parent",
        "type",
        "budget",
        "currency",
        "transaction_count",
        "status"
      ]}
    />
  );
}

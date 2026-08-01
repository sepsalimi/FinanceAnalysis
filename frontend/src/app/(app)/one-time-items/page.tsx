import { SectionPage } from "@/components/data/section-page";

export default function OneTimeItemsPage() {
  return (
    <SectionPage
      title="One Time Items"
      description="Review unusual or non-recurring financial events detected by the backend."
      endpoint="/one-time-items"
      preferredColumns={[
        "date",
        "description",
        "amount",
        "category",
        "reason",
        "status"
      ]}
    />
  );
}

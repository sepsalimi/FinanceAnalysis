import { SectionPage } from "@/components/data/section-page";

export default function DataQualityPage() {
  return (
    <SectionPage
      title="Data Quality"
      description="Track duplicates, missing categories, failed imports, account gaps, and confidence checks."
      endpoint="/data-quality"
      preferredColumns={[
        "check",
        "severity",
        "affected_records",
        "status",
        "last_seen_at",
        "recommendation"
      ]}
    />
  );
}

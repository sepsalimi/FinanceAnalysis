import { SectionPage } from "@/components/data/section-page";

export default function RulesPage() {
  return (
    <SectionPage
      title="Rules"
      description="Review categorization, matching, exclusion, and transfer detection rules."
      endpoint="/rules"
      preferredColumns={[
        "name",
        "condition",
        "action",
        "priority",
        "enabled",
        "last_applied_at"
      ]}
    />
  );
}

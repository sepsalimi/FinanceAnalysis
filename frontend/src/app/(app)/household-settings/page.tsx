import { SectionPage } from "@/components/data/section-page";

export default function HouseholdSettingsPage() {
  return (
    <SectionPage
      title="Household Settings"
      description="View household configuration, members, preferences, currency, timezone, and permissions."
      endpoint="/household-settings"
      preferredColumns={[
        "household_name",
        "currency",
        "timezone",
        "member_count",
        "role",
        "updated_at"
      ]}
    />
  );
}

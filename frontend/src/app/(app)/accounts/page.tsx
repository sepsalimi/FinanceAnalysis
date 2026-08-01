import { SectionPage } from "@/components/data/section-page";

export default function AccountsPage() {
  return (
    <SectionPage
      title="Accounts"
      description="Monitor linked and imported accounts, balances, institutions, and sync states."
      endpoint="/accounts"
      preferredColumns={[
        "name",
        "institution",
        "type",
        "balance",
        "currency",
        "last_synced_at",
        "status"
      ]}
    />
  );
}

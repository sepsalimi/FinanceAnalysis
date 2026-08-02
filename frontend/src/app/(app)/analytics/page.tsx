import { SectionPage } from "@/components/data/section-page";

export default function AnalyticsPage() {
  return (
    <SectionPage
      title="Analytics"
      description="Explore backend-generated insights, trends, cohorts, and financial intelligence outputs."
      endpoint="/analytics"
      preferredColumns={["name", "metric", "value", "period", "status"]}
    />
  );
}

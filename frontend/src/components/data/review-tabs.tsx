"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { RecordTable } from "@/components/data/record-table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle
} from "@/components/ui/card";
import { apiFetch, withQuery } from "@/lib/api";
import type { ApiCollection, RecordLike } from "@/types/api";

const reviewTabs = [
  { label: "All", value: "all" },
  { label: "For Review", value: "for_review" },
  { label: "Assessed", value: "assessed" },
  { label: "Pending Category", value: "pending_category" },
  { label: "Pending Match", value: "pending_match" },
  { label: "Possible Duplicates", value: "possible_duplicates" },
  { label: "Possible Transfers", value: "possible_transfers" },
  { label: "Excluded", value: "excluded" },
  { label: "Failed", value: "failed" }
];

function extractItems(payload: ApiCollection<RecordLike> | RecordLike[]) {
  if (Array.isArray(payload)) {
    return payload;
  }

  return payload.items ?? payload.results ?? payload.data ?? [];
}

export function ReviewTabs() {
  const [activeTab, setActiveTab] = useState(reviewTabs[0].value);
  const endpoint = withQuery("/review", {
    status: activeTab === "all" ? undefined : activeTab
  });

  const query = useQuery({
    queryKey: ["review", activeTab],
    queryFn: () => apiFetch<ApiCollection<RecordLike> | RecordLike[]>(endpoint)
  });

  const items = query.data ? extractItems(query.data) : [];

  return (
    <div className="space-y-6">
      <div>
        <Badge variant="pending" className="mb-3">
          Review workbench
        </Badge>
        <h1 className="text-3xl font-extrabold tracking-tight sm:text-4xl">
          Review
        </h1>
        <p className="mt-2 max-w-3xl text-muted-foreground">
          Work through categorization, matching, duplicate, transfer, exclusion,
          and failed import queues from the API.
        </p>
      </div>

      <div className="flex flex-wrap gap-2 rounded-3xl border bg-card/80 p-2">
        {reviewTabs.map((tab) => (
          <Button
            key={tab.value}
            type="button"
            size="sm"
            variant={activeTab === tab.value ? "default" : "ghost"}
            className="rounded-full"
            onClick={() => setActiveTab(tab.value)}
          >
            {tab.label}
          </Button>
        ))}
      </div>

      {query.isLoading ? (
        <Card>
          <CardHeader>
            <CardTitle>Loading review queue</CardTitle>
            <CardDescription>
              Fetching the latest records for the selected tab.
            </CardDescription>
          </CardHeader>
        </Card>
      ) : query.isError ? (
        <Card className="border-warning/50 bg-warning/10">
          <CardHeader>
            <CardTitle>Could not load review records</CardTitle>
            <CardDescription>
              Check that the API is running and serving {endpoint}.
            </CardDescription>
          </CardHeader>
        </Card>
      ) : (
        <RecordTable
          data={items}
          preferredColumns={[
            "date",
            "description",
            "amount",
            "category",
            "match_status",
            "review_status",
            "confidence"
          ]}
        />
      )}
    </div>
  );
}

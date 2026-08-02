"use client";

import { useQuery } from "@tanstack/react-query";
import { AlertCircle, RefreshCcw } from "lucide-react";

import { RecordTable } from "@/components/data/record-table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from "@/components/ui/card";
import { apiFetch } from "@/lib/api";
import type { ApiCollection, RecordLike } from "@/types/api";

function extractItems(payload: ApiCollection<RecordLike> | RecordLike[]) {
  if (Array.isArray(payload)) {
    return payload;
  }

  return payload.items ?? payload.results ?? payload.data ?? [];
}

export function SectionPage({
  title,
  description,
  endpoint,
  preferredColumns
}: {
  title: string;
  description: string;
  endpoint: string;
  preferredColumns?: string[];
}) {
  const query = useQuery({
    queryKey: ["section", endpoint],
    queryFn: () => apiFetch<ApiCollection<RecordLike> | RecordLike[]>(endpoint)
  });

  const items = query.data ? extractItems(query.data) : [];

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <Badge variant="secondary" className="mb-3">
            Live API
          </Badge>
          <h1 className="text-3xl font-extrabold tracking-tight sm:text-4xl">
            {title}
          </h1>
          <p className="mt-2 max-w-3xl text-muted-foreground">{description}</p>
        </div>
        <Button
          type="button"
          variant="outline"
          onClick={() => void query.refetch()}
          disabled={query.isFetching}
        >
          <RefreshCcw className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      {query.isLoading ? (
        <Card>
          <CardHeader>
            <CardTitle>Loading {title.toLowerCase()}</CardTitle>
            <CardDescription>
              Fetching the latest records from the household API.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3">
            <div className="h-12 animate-pulse rounded-2xl bg-muted" />
            <div className="h-12 animate-pulse rounded-2xl bg-muted/80" />
            <div className="h-12 animate-pulse rounded-2xl bg-muted/60" />
          </CardContent>
        </Card>
      ) : query.isError ? (
        <Card className="border-warning/50 bg-warning/10">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5" />
              Could not load this section
            </CardTitle>
            <CardDescription>
              Check that the API is running and serving {endpoint}.
            </CardDescription>
          </CardHeader>
        </Card>
      ) : (
        <RecordTable data={items} preferredColumns={preferredColumns} />
      )}
    </div>
  );
}

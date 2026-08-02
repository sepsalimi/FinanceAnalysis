"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { CheckCircle2 } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";

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
import { apiFetch, withQuery } from "@/lib/api";
import type { ApiCollection, RecordLike } from "@/types/api";

function extractItems(payload: ApiCollection<RecordLike> | RecordLike[]) {
  if (Array.isArray(payload)) {
    return payload;
  }

  return payload.items ?? payload.results ?? payload.data ?? [];
}

function ImportConfirmContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const importId = searchParams.get("importId");
  const endpoint = withQuery("/imports/confirm", {
    import_id: importId
  });

  const confirmationQuery = useQuery({
    queryKey: ["import-confirm", importId],
    queryFn: () => apiFetch<ApiCollection<RecordLike> | RecordLike[]>(endpoint)
  });

  const confirmMutation = useMutation({
    mutationFn: () =>
      apiFetch("/imports/confirm", {
        method: "POST",
        body: JSON.stringify({ import_id: importId })
      }),
    onSuccess: () => router.push("/transactions")
  });

  const items = confirmationQuery.data
    ? extractItems(confirmationQuery.data)
    : [];

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <Badge variant="success" className="mb-3">
            Import flow
          </Badge>
          <h1 className="text-3xl font-extrabold tracking-tight sm:text-4xl">
            Confirm import
          </h1>
          <p className="mt-2 max-w-3xl text-muted-foreground">
            Review the backend confirmation set before committing transactions
            into the household ledger.
          </p>
        </div>
        <Button
          type="button"
          className="rounded-3xl"
          disabled={confirmMutation.isPending}
          onClick={() => confirmMutation.mutate()}
        >
          <CheckCircle2 className="mr-2 h-4 w-4" />
          {confirmMutation.isPending ? "Confirming..." : "Confirm import"}
        </Button>
      </div>

      {confirmMutation.isError ? (
        <Card className="border-warning/50 bg-warning/10">
          <CardHeader>
            <CardTitle>Import confirmation failed</CardTitle>
            <CardDescription>
              Check that the API can confirm this import.
            </CardDescription>
          </CardHeader>
        </Card>
      ) : null}

      {confirmationQuery.isLoading ? (
        <Card>
          <CardHeader>
            <CardTitle>Loading confirmation details</CardTitle>
            <CardDescription>
              Fetching the final import preview from the backend.
            </CardDescription>
          </CardHeader>
        </Card>
      ) : confirmationQuery.isError ? (
        <Card className="border-warning/50 bg-warning/10">
          <CardHeader>
            <CardTitle>Could not load confirmation details</CardTitle>
            <CardDescription>
              Check that the API is running and serving {endpoint}.
            </CardDescription>
          </CardHeader>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Rows ready for confirmation</CardTitle>
            <CardDescription>
              These records come directly from the confirmation endpoint.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <RecordTable
              data={items}
              preferredColumns={[
                "date",
                "description",
                "amount",
                "currency",
                "account",
                "category",
                "status"
              ]}
            />
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default function ImportConfirmPage() {
  return (
    <Suspense
      fallback={
        <Card>
          <CardHeader>
            <CardTitle>Loading confirmation</CardTitle>
            <CardDescription>Preparing the import confirmation step.</CardDescription>
          </CardHeader>
        </Card>
      }
    >
      <ImportConfirmContent />
    </Suspense>
  );
}

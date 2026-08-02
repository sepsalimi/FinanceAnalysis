"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowRight, Wand2 } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, Suspense, useState } from "react";

import { RecordTable } from "@/components/data/record-table";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { apiFetch, withQuery } from "@/lib/api";
import type { ApiCollection, RecordLike } from "@/types/api";

function extractItems(payload: ApiCollection<RecordLike> | RecordLike[]) {
  if (Array.isArray(payload)) {
    return payload;
  }

  return payload.items ?? payload.results ?? payload.data ?? [];
}

function ImportInterpretationContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const importId = searchParams.get("importId");
  const [corrections, setCorrections] = useState("");
  const endpoint = withQuery("/imports/interpretation", {
    import_id: importId
  });

  const previewQuery = useQuery({
    queryKey: ["import-interpretation", importId],
    queryFn: () => apiFetch<ApiCollection<RecordLike> | RecordLike[]>(endpoint)
  });

  const correctionMutation = useMutation({
    mutationFn: () =>
      apiFetch("/imports/interpretation", {
        method: "POST",
        body: JSON.stringify({
          import_id: importId,
          corrections: corrections ? JSON.parse(corrections) : undefined
        })
      }),
    onSuccess: () =>
      router.push(
        importId
          ? `/imports/confirm?importId=${encodeURIComponent(importId)}`
          : "/imports/confirm"
      )
  });

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    correctionMutation.mutate();
  }

  const items = previewQuery.data ? extractItems(previewQuery.data) : [];

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.22em] text-primary">
          Import flow
        </p>
        <h1 className="mt-2 text-3xl font-extrabold tracking-tight sm:text-4xl">
          Interpretation preview
        </h1>
        <p className="mt-2 max-w-3xl text-muted-foreground">
          Review the backend interpretation, then submit structured corrections
          before confirmation.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Step 2: Preview and correct</CardTitle>
          <CardDescription>
            Preview data is fetched from {endpoint}. Corrections are posted back
            as JSON.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={onSubmit}>
            <div className="space-y-2">
              <Label htmlFor="corrections">Corrections JSON</Label>
              <textarea
                id="corrections"
                className="min-h-32 w-full rounded-3xl border bg-background/80 p-4 text-sm outline-none ring-offset-background placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-ring"
                value={corrections}
                onChange={(event) => setCorrections(event.target.value)}
                placeholder='{"column_mapping":{"Date":"date","Amount":"amount"}}'
              />
            </div>

            {correctionMutation.isError ? (
              <p className="rounded-2xl bg-warning/15 p-3 text-sm text-warning-foreground">
                Correction submission failed. Confirm the JSON is valid and the
                API is available.
              </p>
            ) : null}

            <Button
              type="submit"
              className="rounded-3xl"
              disabled={correctionMutation.isPending}
            >
              <Wand2 className="mr-2 h-4 w-4" />
              {correctionMutation.isPending
                ? "Saving interpretation..."
                : "Save interpretation"}
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </form>
        </CardContent>
      </Card>

      {previewQuery.isLoading ? (
        <Card>
          <CardHeader>
            <CardTitle>Loading preview</CardTitle>
            <CardDescription>
              Fetching interpreted rows from the backend.
            </CardDescription>
          </CardHeader>
        </Card>
      ) : previewQuery.isError ? (
        <Card className="border-warning/50 bg-warning/10">
          <CardHeader>
            <CardTitle>Could not load interpretation preview</CardTitle>
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
            "currency",
            "account",
            "category",
            "confidence"
          ]}
        />
      )}
    </div>
  );
}

export default function ImportInterpretationPage() {
  return (
    <Suspense
      fallback={
        <Card>
          <CardHeader>
            <CardTitle>Loading interpretation</CardTitle>
            <CardDescription>Preparing the import interpretation step.</CardDescription>
          </CardHeader>
        </Card>
      }
    >
      <ImportInterpretationContent />
    </Suspense>
  );
}

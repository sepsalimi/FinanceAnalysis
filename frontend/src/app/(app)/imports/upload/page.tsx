"use client";

/**
 * Import upload step: stores the file via the backend and starts interpretation.
 */

import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowRight, FileUp } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiFetch } from "@/lib/api";
import type { ApiCollection, RecordLike } from "@/types/api";

type UploadResponse = {
  import_id?: string;
  id?: string;
};

function extractItems(payload: ApiCollection<RecordLike> | RecordLike[]) {
  if (Array.isArray(payload)) return payload;
  return payload.items ?? payload.results ?? payload.data ?? [];
}

export default function ImportUploadPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [sourceName, setSourceName] = useState("");
  const [accountId, setAccountId] = useState("");

  const accountsQuery = useQuery({
    queryKey: ["accounts"],
    queryFn: () => apiFetch<ApiCollection<RecordLike> | RecordLike[]>("/accounts")
  });

  const accounts = useMemo(
    () => (accountsQuery.data ? extractItems(accountsQuery.data) : []),
    [accountsQuery.data]
  );

  const uploadMutation = useMutation({
    mutationFn: () => {
      const formData = new FormData();
      if (file) formData.append("file", file);
      if (sourceName) formData.append("source_name", sourceName);
      if (accountId) formData.append("financial_account_id", accountId);
      return apiFetch<UploadResponse>("/imports/upload", {
        method: "POST",
        body: formData
      });
    },
    onSuccess: (response) => {
      const importId = response.import_id ?? response.id;
      router.push(
        importId
          ? `/imports/interpretation?importId=${encodeURIComponent(importId)}`
          : "/imports/interpretation"
      );
    }
  });

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file) return;
    uploadMutation.mutate();
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.22em] text-primary">
          Import flow
        </p>
        <h1 className="mt-2 text-3xl font-extrabold tracking-tight sm:text-4xl">
          Upload financial data
        </h1>
        <p className="mt-2 text-muted-foreground">
          CSV and Excel files are stored securely, then interpreted before any
          financial records are created.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Step 1: Upload</CardTitle>
          <CardDescription>
            Choose an account when importing bank or card statements.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form className="space-y-5" onSubmit={onSubmit}>
            <div className="space-y-2">
              <Label htmlFor="source_name">Source name</Label>
              <Input
                id="source_name"
                value={sourceName}
                onChange={(event) => setSourceName(event.target.value)}
                placeholder="Bank, card, Splitwise, or workbook"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="account">Financial account</Label>
              <select
                id="account"
                className="flex h-11 w-full rounded-2xl border bg-background px-3 text-sm"
                value={accountId}
                onChange={(event) => setAccountId(event.target.value)}
              >
                <option value="">No account selected</option>
                {accounts.map((account) => (
                  <option key={String(account.id)} value={String(account.id)}>
                    {String(account.account_name ?? account.id)}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="file">File</Label>
              <Input
                id="file"
                type="file"
                accept=".csv,.xlsx,.xlsm"
                onChange={(event) =>
                  setFile(event.target.files ? event.target.files[0] : null)
                }
              />
            </div>

            {uploadMutation.isError ? (
              <p className="rounded-2xl bg-warning/15 p-3 text-sm text-warning-foreground">
                Upload failed. Confirm the API is available and accepts this
                file format.
              </p>
            ) : null}

            <Button
              type="submit"
              className="rounded-3xl"
              disabled={!file || uploadMutation.isPending}
            >
              <FileUp className="mr-2 h-4 w-4" />
              {uploadMutation.isPending ? "Uploading..." : "Upload and interpret"}
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

"use client";

import { useMutation } from "@tanstack/react-query";
import { ArrowRight, FileUp } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

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

type UploadResponse = {
  import_id?: string;
  id?: string;
};

export default function ImportUploadPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [sourceName, setSourceName] = useState("");

  const uploadMutation = useMutation({
    mutationFn: () => {
      const formData = new FormData();

      if (file) {
        formData.append("file", file);
      }

      if (sourceName) {
        formData.append("source_name", sourceName);
      }

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

    if (!file) {
      return;
    }

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
          Send statements, exports, or transaction files to the backend for
          interpretation.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Step 1: Upload</CardTitle>
          <CardDescription>
            The uploaded file is posted to /imports/upload with credentials.
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
                placeholder="Bank, card, payroll, or export source"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="file">File</Label>
              <Input
                id="file"
                type="file"
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
              disabled={!file || uploadMutation.isPending}
              className="rounded-3xl"
            >
              <FileUp className="mr-2 h-4 w-4" />
              {uploadMutation.isPending ? "Uploading..." : "Upload and preview"}
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

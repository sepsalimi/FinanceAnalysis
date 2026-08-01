"use client";

/**
 * Financial accounts list and create form.
 * Account data is loaded from the API; balances are never hardcoded.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { useState } from "react";

import { RecordTable } from "@/components/data/record-table";
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

const ACCOUNT_TYPES = [
  "chequing",
  "savings",
  "credit_card",
  "line_of_credit",
  "loan",
  "mortgage",
  "investment",
  "cash",
  "other"
];

function extractItems(payload: ApiCollection<RecordLike> | RecordLike[]) {
  if (Array.isArray(payload)) return payload;
  return payload.items ?? payload.results ?? payload.data ?? [];
}

export default function AccountsPage() {
  const queryClient = useQueryClient();
  const [accountName, setAccountName] = useState("");
  const [accountType, setAccountType] = useState("chequing");
  const [currency, setCurrency] = useState("");
  const [openingBalance, setOpeningBalance] = useState("0");

  const accountsQuery = useQuery({
    queryKey: ["accounts"],
    queryFn: () => apiFetch<ApiCollection<RecordLike> | RecordLike[]>("/accounts")
  });

  const createMutation = useMutation({
    mutationFn: () =>
      apiFetch("/accounts", {
        method: "POST",
        body: JSON.stringify({
          account_name: accountName,
          account_type: accountType,
          currency: currency || undefined,
          opening_balance: openingBalance || "0"
        })
      }),
    onSuccess: async () => {
      setAccountName("");
      setOpeningBalance("0");
      await queryClient.invalidateQueries({ queryKey: ["accounts"] });
    }
  });

  const items = accountsQuery.data ? extractItems(accountsQuery.data) : [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight sm:text-4xl">
          Accounts
        </h1>
        <p className="mt-2 max-w-3xl text-muted-foreground">
          Create bank, credit card, savings, investment, loan, and cash accounts
          before importing statements.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Create account</CardTitle>
          <CardDescription>
            Ownership can be assigned to household members after creation.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form
            className="grid gap-4 md:grid-cols-2"
            onSubmit={(event) => {
              event.preventDefault();
              if (!accountName.trim()) return;
              createMutation.mutate();
            }}
          >
            <div className="space-y-2">
              <Label htmlFor="account_name">Account name</Label>
              <Input
                id="account_name"
                value={accountName}
                onChange={(event) => setAccountName(event.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="account_type">Account type</Label>
              <select
                id="account_type"
                className="flex h-11 w-full rounded-2xl border bg-background px-3 text-sm"
                value={accountType}
                onChange={(event) => setAccountType(event.target.value)}
              >
                {ACCOUNT_TYPES.map((type) => (
                  <option key={type} value={type}>
                    {type.replaceAll("_", " ")}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="currency">Currency override</Label>
              <Input
                id="currency"
                value={currency}
                onChange={(event) => setCurrency(event.target.value.toUpperCase())}
                placeholder="Uses household default when empty"
                maxLength={3}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="opening_balance">Opening balance</Label>
              <Input
                id="opening_balance"
                value={openingBalance}
                onChange={(event) => setOpeningBalance(event.target.value)}
              />
            </div>
            <div className="md:col-span-2">
              <Button
                type="submit"
                className="rounded-3xl"
                disabled={createMutation.isPending}
              >
                <Plus className="mr-2 h-4 w-4" />
                {createMutation.isPending ? "Creating..." : "Create account"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Household accounts</CardTitle>
          <CardDescription>Loaded from /accounts</CardDescription>
        </CardHeader>
        <CardContent>
          <RecordTable
            data={items}
            preferredColumns={[
              "account_name",
              "account_type",
              "currency",
              "opening_balance",
              "current_reconciled_balance",
              "is_active"
            ]}
          />
        </CardContent>
      </Card>
    </div>
  );
}

"use client";

/**
 * Household settings including LLM provider configuration.
 * API keys are sent to the backend only and never stored in git or localStorage.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { KeyRound, Save, Smartphone } from "lucide-react";
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
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

type LlmSettings = {
  provider?: string;
  model?: string;
  has_api_key?: boolean;
  api_key_set?: boolean;
};

type SettingsPayload = {
  id?: string;
  name?: string;
  default_currency?: string;
  timezone?: string;
  llm?: LlmSettings;
  members?: Array<{ id: string; display_name: string; is_active: boolean }>;
};

export default function HouseholdSettingsPage() {
  const queryClient = useQueryClient();
  const settingsQuery = useQuery({
    queryKey: ["household-settings"],
    queryFn: () =>
      apiFetch<{ settings?: SettingsPayload; items?: SettingsPayload[] }>(
        "/household-settings"
      )
  });

  const settings =
    settingsQuery.data?.settings ?? settingsQuery.data?.items?.[0] ?? null;

  const [name, setName] = useState("");
  const [currency, setCurrency] = useState("");
  const [timezone, setTimezone] = useState("");
  const [provider, setProvider] = useState("stub");
  const [model, setModel] = useState("stub-v1");
  const [apiKey, setApiKey] = useState("");
  const [clearKey, setClearKey] = useState(false);

  useEffect(() => {
    if (!settings) return;
    setName(settings.name ?? "");
    setCurrency(settings.default_currency ?? "");
    setTimezone(settings.timezone ?? "");
    setProvider(settings.llm?.provider ?? "stub");
    setModel(settings.llm?.model ?? "stub-v1");
  }, [settings]);

  const saveMutation = useMutation({
    mutationFn: () =>
      apiFetch("/household-settings", {
        method: "PATCH",
        body: JSON.stringify({
          name,
          default_currency: currency,
          timezone,
          llm: {
            provider,
            model,
            api_key: apiKey.trim() || undefined,
            clear_api_key: clearKey
          }
        })
      }),
    onSuccess: async () => {
      setApiKey("");
      setClearKey(false);
      await queryClient.invalidateQueries({ queryKey: ["household-settings"] });
    }
  });

  const keyConfigured = Boolean(
    settings?.llm?.has_api_key || settings?.llm?.api_key_set
  );

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <Badge variant="secondary" className="mb-3">
          Household settings
        </Badge>
        <h1 className="text-3xl font-extrabold tracking-tight sm:text-4xl">
          Household Settings
        </h1>
        <p className="mt-2 max-w-3xl text-muted-foreground">
          Configure currency, members, and the LLM used to interpret uploads and
          categorize transactions. Keys are encrypted in the database and never
          committed to git.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Household profile</CardTitle>
          <CardDescription>Basic household identity and locale.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2 md:col-span-2">
            <Label htmlFor="name">Household name</Label>
            <Input id="name" value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="currency">Default currency</Label>
            <Input
              id="currency"
              value={currency}
              maxLength={3}
              onChange={(e) => setCurrency(e.target.value.toUpperCase())}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="timezone">Timezone</Label>
            <Input
              id="timezone"
              value={timezone}
              onChange={(e) => setTimezone(e.target.value)}
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <KeyRound className="h-5 w-5" />
            LLM provider
          </CardTitle>
          <CardDescription>
            Optional. Without a key, the app uses the built-in heuristic stub so
            imports still work. With a key, file mapping and categorization use
            your chosen provider.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="provider">Provider</Label>
              <select
                id="provider"
                className="flex h-11 w-full rounded-2xl border bg-background px-3 text-sm"
                value={provider}
                onChange={(e) => setProvider(e.target.value)}
              >
                <option value="stub">Stub (no API key)</option>
                <option value="openai">OpenAI</option>
                <option value="anthropic">Anthropic</option>
                <option value="gemini">Google Gemini</option>
              </select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="model">Model</Label>
              <Input
                id="model"
                value={model}
                onChange={(e) => setModel(e.target.value)}
                placeholder="gpt-4o-mini"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="api_key">API key</Label>
            <Input
              id="api_key"
              type="password"
              autoComplete="off"
              value={apiKey}
              onChange={(e) => {
                setApiKey(e.target.value);
                setClearKey(false);
              }}
              placeholder={
                keyConfigured
                  ? "Key is saved. Paste a new key to replace it."
                  : "Paste provider API key"
              }
            />
            <p className="text-sm text-muted-foreground">
              Status:{" "}
              {keyConfigured ? "API key configured on server" : "No API key saved"}
            </p>
          </div>

          {keyConfigured ? (
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={clearKey}
                onChange={(e) => setClearKey(e.target.checked)}
              />
              Remove saved API key
            </label>
          ) : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Smartphone className="h-5 w-5" />
            Install on phone
          </CardTitle>
          <CardDescription>
            This app is installable as a Progressive Web App. On iPhone use Share
            → Add to Home Screen. On Android use the browser menu → Install app.
          </CardDescription>
        </CardHeader>
      </Card>

      {settings?.members?.length ? (
        <Card>
          <CardHeader>
            <CardTitle>Members</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {settings.members.map((member) => (
              <div
                key={member.id}
                className="flex items-center justify-between rounded-2xl border px-4 py-3"
              >
                <span className="font-medium">{member.display_name}</span>
                <Badge variant={member.is_active ? "success" : "secondary"}>
                  {member.is_active ? "Active" : "Inactive"}
                </Badge>
              </div>
            ))}
          </CardContent>
        </Card>
      ) : null}

      {saveMutation.isError ? (
        <p className="rounded-2xl bg-warning/15 p-3 text-sm text-warning-foreground">
          Could not save settings. Confirm the API is running and you have write
          access.
        </p>
      ) : null}
      {saveMutation.isSuccess ? (
        <p className="rounded-2xl bg-success/15 p-3 text-sm text-success-foreground">
          Settings saved.
        </p>
      ) : null}

      <Button
        type="button"
        className="rounded-3xl"
        disabled={saveMutation.isPending || settingsQuery.isLoading}
        onClick={() => saveMutation.mutate()}
      >
        <Save className="mr-2 h-4 w-4" />
        {saveMutation.isPending ? "Saving..." : "Save settings"}
      </Button>
    </div>
  );
}

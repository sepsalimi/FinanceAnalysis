"use client";

import { useQuery } from "@tanstack/react-query";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from "@/components/ui/card";
import { apiFetch } from "@/lib/api";
import { decimalToNumber, formatMoney, formatPercent } from "@/lib/format";
import type { ApiCollection, CashFlowPoint, HouseholdSummary } from "@/types/api";

function extractCashFlow(payload: ApiCollection<CashFlowPoint> | CashFlowPoint[]) {
  if (Array.isArray(payload)) {
    return payload;
  }

  return payload.items ?? payload.results ?? payload.data ?? [];
}

export function DashboardView() {
  const summaryQuery = useQuery({
    queryKey: ["dashboard-summary"],
    queryFn: () => apiFetch<HouseholdSummary>("/dashboard/summary")
  });

  const cashFlowQuery = useQuery({
    queryKey: ["dashboard-cash-flow"],
    queryFn: () =>
      apiFetch<ApiCollection<CashFlowPoint> | CashFlowPoint[]>("/cash-flow")
  });

  const summary = summaryQuery.data;
  const currency = summary?.currency ?? "USD";
  const cashFlow = cashFlowQuery.data ? extractCashFlow(cashFlowQuery.data) : [];
  const chartData = cashFlow.map((point) => ({
    period: point.period,
    income: decimalToNumber(point.income) ?? 0,
    expenses: decimalToNumber(point.expenses) ?? 0,
    net: decimalToNumber(point.net) ?? 0
  }));

  const summaryCards = [
    {
      label: "Net worth",
      value: formatMoney(summary?.net_worth, currency),
      tone: "bg-primary/10"
    },
    {
      label: "Cash balance",
      value: formatMoney(summary?.cash_balance, currency),
      tone: "bg-success/15"
    },
    {
      label: "Monthly income",
      value: formatMoney(summary?.monthly_income, currency),
      tone: "bg-secondary/70"
    },
    {
      label: "Monthly expenses",
      value: formatMoney(summary?.monthly_expenses, currency),
      tone: "bg-warning/15"
    }
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <Badge variant="secondary" className="mb-3">
            Household command center
          </Badge>
          <h1 className="text-3xl font-extrabold tracking-tight sm:text-5xl">
            Financial intelligence dashboard
          </h1>
          <p className="mt-3 max-w-3xl text-muted-foreground">
            A live view of cash flow, review queues, and household financial
            health from your API.
          </p>
        </div>
        <Card className="min-w-64 border-primary/25 bg-primary/10">
          <CardContent className="p-5">
            <p className="text-sm font-semibold text-muted-foreground">
              Savings rate
            </p>
            <p className="mt-2 text-3xl font-extrabold">
              {formatPercent(summary?.savings_rate)}
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {summaryCards.map((card) => (
          <Card key={card.label} className={card.tone}>
            <CardContent className="p-5">
              <p className="text-sm font-semibold text-muted-foreground">
                {card.label}
              </p>
              <p className="mt-3 text-2xl font-extrabold">{card.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.5fr_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Cash-flow trend</CardTitle>
            <CardDescription>
              Rendered from API-provided periods and decimal string amounts.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {cashFlowQuery.isLoading ? (
              <div className="h-80 animate-pulse rounded-3xl bg-muted" />
            ) : chartData.length ? (
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData} margin={{ left: 8, right: 8 }}>
                    <defs>
                      <linearGradient id="income" x1="0" x2="0" y1="0" y2="1">
                        <stop
                          offset="5%"
                          stopColor="hsl(var(--primary))"
                          stopOpacity={0.5}
                        />
                        <stop
                          offset="95%"
                          stopColor="hsl(var(--primary))"
                          stopOpacity={0}
                        />
                      </linearGradient>
                      <linearGradient id="expenses" x1="0" x2="0" y1="0" y2="1">
                        <stop
                          offset="5%"
                          stopColor="hsl(var(--warning))"
                          stopOpacity={0.42}
                        />
                        <stop
                          offset="95%"
                          stopColor="hsl(var(--warning))"
                          stopOpacity={0}
                        />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                    <XAxis dataKey="period" stroke="hsl(var(--muted-foreground))" />
                    <YAxis stroke="hsl(var(--muted-foreground))" />
                    <Tooltip
                      formatter={(value) =>
                        formatMoney(String(value), currency, {
                          maximumFractionDigits: 0
                        })
                      }
                      contentStyle={{
                        borderRadius: "18px",
                        borderColor: "hsl(var(--border))",
                        background: "hsl(var(--card))"
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="income"
                      stroke="hsl(var(--primary))"
                      fill="url(#income)"
                      strokeWidth={3}
                    />
                    <Area
                      type="monotone"
                      dataKey="expenses"
                      stroke="hsl(var(--warning))"
                      fill="url(#expenses)"
                      strokeWidth={3}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="flex h-80 items-center justify-center rounded-3xl bg-muted/60 text-center">
                <div>
                  <p className="font-bold">No cash-flow series returned</p>
                  <p className="mt-2 text-sm text-muted-foreground">
                    The chart will appear when /cash-flow returns periods.
                  </p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Operational signals</CardTitle>
            <CardDescription>
              Live queue and data quality indicators from the summary endpoint.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-3xl bg-secondary/70 p-5">
              <p className="text-sm font-semibold text-muted-foreground">
                Pending review
              </p>
              <p className="mt-2 text-3xl font-extrabold">
                {summary?.pending_review_count ?? "—"}
              </p>
            </div>
            <div className="rounded-3xl bg-success/15 p-5">
              <p className="text-sm font-semibold text-muted-foreground">
                Data quality score
              </p>
              <p className="mt-2 text-3xl font-extrabold">
                {formatPercent(summary?.data_quality_score)}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

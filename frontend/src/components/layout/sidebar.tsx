"use client";

import {
  AreaChart,
  Banknote,
  BarChart3,
  ClipboardCheck,
  DatabaseZap,
  Gauge,
  Landmark,
  Moon,
  ReceiptText,
  RefreshCcw,
  Scale,
  Settings,
  Sparkles,
  Sun,
  Tag,
  UploadCloud,
  WalletCards
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTheme } from "next-themes";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: Gauge },
  { name: "Transactions", href: "/transactions", icon: ReceiptText },
  { name: "Review", href: "/review", icon: ClipboardCheck },
  { name: "Imports", href: "/imports/upload", icon: UploadCloud },
  { name: "Cash Flow", href: "/cash-flow", icon: AreaChart },
  { name: "One Time Items", href: "/one-time-items", icon: Sparkles },
  { name: "Analytics", href: "/analytics", icon: BarChart3 },
  { name: "Accounts", href: "/accounts", icon: WalletCards },
  { name: "Assets and Debts", href: "/assets-and-debts", icon: Landmark },
  { name: "Categories", href: "/categories", icon: Tag },
  { name: "Rules", href: "/rules", icon: RefreshCcw },
  { name: "Data Quality", href: "/data-quality", icon: DatabaseZap },
  { name: "Household Settings", href: "/household-settings", icon: Settings }
];

export function Sidebar() {
  const pathname = usePathname();
  const { theme, setTheme } = useTheme();
  const isDark = theme === "dark";

  return (
    <aside className="flex h-full flex-col rounded-[2rem] border bg-card/88 p-4 shadow-soft backdrop-blur-xl">
      <Link href="/dashboard" className="mb-6 flex items-center gap-3 px-2">
        <div className="flex h-12 w-12 items-center justify-center rounded-3xl bg-primary text-primary-foreground shadow-glow">
          <Banknote className="h-6 w-6" />
        </div>
        <div>
          <p className="text-sm font-semibold text-muted-foreground">
            Household
          </p>
          <h1 className="text-lg font-extrabold leading-tight">
            Financial IQ
          </h1>
        </div>
      </Link>

      <nav className="min-h-0 flex-1 space-y-1 overflow-y-auto pr-1">
        {navigation.map((item) => {
          const isActive =
            pathname === item.href ||
            (item.href !== "/dashboard" && pathname.startsWith(item.href));
          const Icon = item.icon;

          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "group flex items-center gap-3 rounded-2xl px-3 py-2.5 text-sm font-semibold text-muted-foreground transition-all hover:bg-accent hover:text-accent-foreground",
                isActive &&
                  "bg-primary text-primary-foreground shadow-glow hover:bg-primary hover:text-primary-foreground"
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>

      <div className="mt-4 rounded-3xl bg-secondary/70 p-3">
        <div className="mb-3 flex items-center gap-2 text-xs font-semibold text-muted-foreground">
          <Scale className="h-4 w-4" />
          Calm, connected money decisions
        </div>
        <Button
          type="button"
          variant="outline"
          className="w-full justify-between rounded-3xl"
          onClick={() => setTheme(isDark ? "light" : "dark")}
        >
          <span>{isDark ? "Light mode" : "Dark mode"}</span>
          {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </Button>
      </div>
    </aside>
  );
}

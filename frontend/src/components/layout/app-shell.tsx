"use client";

import { Menu } from "lucide-react";
import { ReactNode, useState } from "react";

import { Button } from "@/components/ui/button";
import { Sidebar } from "@/components/layout/sidebar";
import { cn } from "@/lib/utils";

export function AppShell({ children }: { children: ReactNode }) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  return (
    <div className="surface-grid min-h-screen p-3 sm:p-5">
      <div className="mx-auto flex min-h-[calc(100vh-2.5rem)] max-w-[1600px] gap-4">
        <div className="hidden w-80 shrink-0 lg:block">
          <div className="sticky top-5 h-[calc(100vh-2.5rem)]">
            <Sidebar />
          </div>
        </div>

        <div
          className={cn(
            "fixed inset-0 z-40 bg-navy/30 backdrop-blur-sm transition-opacity lg:hidden",
            isSidebarOpen
              ? "pointer-events-auto opacity-100"
              : "pointer-events-none opacity-0"
          )}
          onClick={() => setIsSidebarOpen(false)}
        />
        <div
          className={cn(
            "fixed bottom-3 left-3 top-3 z-50 w-[min(22rem,calc(100vw-1.5rem))] transition-transform lg:hidden",
            isSidebarOpen ? "translate-x-0" : "-translate-x-[120%]"
          )}
        >
          <Sidebar />
        </div>

        <main className="min-w-0 flex-1">
          <header className="mb-4 flex items-center justify-between rounded-[2rem] border bg-card/82 px-4 py-3 shadow-soft backdrop-blur-xl lg:hidden">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-primary">
                Financial IQ
              </p>
              <h1 className="text-lg font-extrabold">Household platform</h1>
            </div>
            <Button
              type="button"
              variant="outline"
              size="icon"
              aria-label="Open navigation"
              onClick={() => setIsSidebarOpen(true)}
            >
              <Menu className="h-5 w-5" />
            </Button>
          </header>

          <div className="min-h-full rounded-[2rem] border bg-background/72 p-4 shadow-soft backdrop-blur-xl sm:p-6 lg:p-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}

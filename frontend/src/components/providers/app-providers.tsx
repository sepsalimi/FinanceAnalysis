"use client";

import { ReactNode } from "react";

import { PwaRegister } from "@/components/providers/pwa-register";
import { QueryProvider } from "@/components/providers/query-provider";
import { ThemeProvider } from "@/components/providers/theme-provider";

export function AppProviders({ children }: { children: ReactNode }) {
  return (
    <ThemeProvider>
      <QueryProvider>
        <PwaRegister />
        {children}
      </QueryProvider>
    </ThemeProvider>
  );
}

"use client";

import { useMutation } from "@tanstack/react-query";
import { ArrowRight, Banknote } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { z } from "zod";

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

const loginSchema = z.object({
  email: z.string().email("Enter a valid email address."),
  password: z.string().min(1, "Password is required.")
});

type LoginFormValues = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const router = useRouter();
  const form = useForm<LoginFormValues>({
    defaultValues: {
      email: "",
      password: ""
    }
  });

  const loginMutation = useMutation({
    mutationFn: (values: LoginFormValues) =>
      apiFetch("/auth/login", {
        method: "POST",
        body: JSON.stringify(values)
      }),
    onSuccess: () => router.push("/dashboard")
  });

  function onSubmit(values: LoginFormValues) {
    const parsed = loginSchema.safeParse(values);

    if (!parsed.success) {
      parsed.error.issues.forEach((issue) => {
        const field = issue.path[0] as keyof LoginFormValues;
        form.setError(field, { message: issue.message });
      });
      return;
    }

    loginMutation.mutate(parsed.data);
  }

  return (
    <main className="surface-grid flex min-h-screen items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-3xl bg-primary text-primary-foreground shadow-glow">
            <Banknote className="h-7 w-7" />
          </div>
          <CardTitle className="text-3xl">Welcome back</CardTitle>
          <CardDescription>
            Sign in to continue to your household financial dashboard.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={form.handleSubmit(onSubmit)}>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                placeholder="you@example.com"
                {...form.register("email")}
              />
              {form.formState.errors.email ? (
                <p className="text-sm text-destructive">
                  {form.formState.errors.email.message}
                </p>
              ) : null}
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                {...form.register("password")}
              />
              {form.formState.errors.password ? (
                <p className="text-sm text-destructive">
                  {form.formState.errors.password.message}
                </p>
              ) : null}
            </div>

            {loginMutation.isError ? (
              <p className="rounded-2xl bg-warning/15 p-3 text-sm text-warning-foreground">
                Unable to sign in. Check your credentials and API status.
              </p>
            ) : null}

            <Button
              type="submit"
              className="w-full rounded-3xl"
              disabled={loginMutation.isPending}
            >
              {loginMutation.isPending ? "Signing in..." : "Sign in"}
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </form>

          <p className="mt-6 text-center text-sm text-muted-foreground">
            New household?{" "}
            <Link href="/register" className="font-semibold text-primary">
              Create an account
            </Link>
          </p>
        </CardContent>
      </Card>
    </main>
  );
}

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

const registerSchema = z.object({
  email: z.string().email("Enter a valid email address."),
  password: z.string().min(8, "Use at least 8 characters."),
  household_name: z.string().min(2, "Household name is required.")
});

type RegisterFormValues = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  const router = useRouter();
  const form = useForm<RegisterFormValues>({
    defaultValues: {
      email: "",
      password: "",
      household_name: ""
    }
  });

  const registerMutation = useMutation({
    mutationFn: (values: RegisterFormValues) =>
      apiFetch("/auth/register", {
        method: "POST",
        body: JSON.stringify(values)
      }),
    onSuccess: () => router.push("/onboarding")
  });

  function onSubmit(values: RegisterFormValues) {
    const parsed = registerSchema.safeParse(values);

    if (!parsed.success) {
      parsed.error.issues.forEach((issue) => {
        const field = issue.path[0] as keyof RegisterFormValues;
        form.setError(field, { message: issue.message });
      });
      return;
    }

    registerMutation.mutate(parsed.data);
  }

  return (
    <main className="surface-grid flex min-h-screen items-center justify-center p-4">
      <Card className="w-full max-w-lg">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-3xl bg-primary text-primary-foreground shadow-glow">
            <Banknote className="h-7 w-7" />
          </div>
          <CardTitle className="text-3xl">Create your household</CardTitle>
          <CardDescription>
            Start with an account, then invite or add household members during
            onboarding.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={form.handleSubmit(onSubmit)}>
            <div className="space-y-2">
              <Label htmlFor="household_name">Household name</Label>
              <Input
                id="household_name"
                autoComplete="organization"
                {...form.register("household_name")}
              />
              {form.formState.errors.household_name ? (
                <p className="text-sm text-destructive">
                  {form.formState.errors.household_name.message}
                </p>
              ) : null}
            </div>

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
                autoComplete="new-password"
                {...form.register("password")}
              />
              {form.formState.errors.password ? (
                <p className="text-sm text-destructive">
                  {form.formState.errors.password.message}
                </p>
              ) : null}
            </div>

            {registerMutation.isError ? (
              <p className="rounded-2xl bg-warning/15 p-3 text-sm text-warning-foreground">
                Unable to register. Check the API status and try again.
              </p>
            ) : null}

            <Button
              type="submit"
              className="w-full rounded-3xl"
              disabled={registerMutation.isPending}
            >
              {registerMutation.isPending ? "Creating..." : "Create account"}
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </form>

          <p className="mt-6 text-center text-sm text-muted-foreground">
            Already registered?{" "}
            <Link href="/login" className="font-semibold text-primary">
              Sign in
            </Link>
          </p>
        </CardContent>
      </Card>
    </main>
  );
}

"use client";

import { useMutation } from "@tanstack/react-query";
import { Plus, Users } from "lucide-react";
import { useRouter } from "next/navigation";
import { type Path, useFieldArray, useForm } from "react-hook-form";
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

const personSchema = z.object({
  name: z.string(),
  email: z.string()
});

const onboardingSchema = z.object({
  household_name: z.string().min(2, "Household name is required."),
  currency: z.string().min(3, "Currency is required."),
  timezone: z.string().min(2, "Timezone is required."),
  people: z
    .array(personSchema)
    .min(1)
    .max(3)
    .superRefine((people, context) => {
      const primaryPerson = people[0];

      if (!primaryPerson?.name.trim()) {
        context.addIssue({
          code: z.ZodIssueCode.custom,
          message: "Person 1 name is required.",
          path: [0, "name"]
        });
      }

      people.forEach((person, index) => {
        if (person.email && !z.string().email().safeParse(person.email).success) {
          context.addIssue({
            code: z.ZodIssueCode.custom,
            message: `Person ${index + 1} email must be valid.`,
            path: [index, "email"]
          });
        }
      });
    })
});

type OnboardingFormValues = z.infer<typeof onboardingSchema>;

export default function OnboardingPage() {
  const router = useRouter();
  const form = useForm<OnboardingFormValues>({
    defaultValues: {
      household_name: "",
      currency: "USD",
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      people: [{ name: "", email: "" }]
    }
  });

  const people = useFieldArray({
    control: form.control,
    name: "people"
  });

  const onboardingMutation = useMutation({
    mutationFn: (values: OnboardingFormValues) =>
      apiFetch("/onboarding", {
        method: "POST",
        body: JSON.stringify({
          ...values,
          people: values.people.filter(
            (person, index) => index === 0 || person.name || person.email
          )
        })
      }),
    onSuccess: () => router.push("/dashboard")
  });

  function onSubmit(values: OnboardingFormValues) {
    form.clearErrors();
    const parsed = onboardingSchema.safeParse(values);

    if (!parsed.success) {
      parsed.error.issues.forEach((issue) => {
        form.setError(issue.path.join(".") as Path<OnboardingFormValues>, {
          message: issue.message
        });
      });
      return;
    }

    onboardingMutation.mutate(parsed.data);
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.22em] text-primary">
          Household setup
        </p>
        <h1 className="mt-2 text-3xl font-extrabold tracking-tight sm:text-4xl">
          Onboard your household
        </h1>
        <p className="mt-2 max-w-3xl text-muted-foreground">
          Configure the household basics before connecting accounts and
          importing financial data.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Household profile
          </CardTitle>
          <CardDescription>
            Person 1 is required. Person 2 and Person 3 are optional.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form className="space-y-6" onSubmit={form.handleSubmit(onSubmit)}>
            <div className="grid gap-4 md:grid-cols-3">
              <div className="space-y-2 md:col-span-3">
                <Label htmlFor="household_name">Household name</Label>
                <Input
                  id="household_name"
                  {...form.register("household_name")}
                />
                {form.formState.errors.household_name ? (
                  <p className="text-sm text-destructive">
                    {form.formState.errors.household_name.message}
                  </p>
                ) : null}
              </div>
              <div className="space-y-2">
                <Label htmlFor="currency">Currency</Label>
                <Input id="currency" {...form.register("currency")} />
                {form.formState.errors.currency ? (
                  <p className="text-sm text-destructive">
                    {form.formState.errors.currency.message}
                  </p>
                ) : null}
              </div>
              <div className="space-y-2 md:col-span-2">
                <Label htmlFor="timezone">Timezone</Label>
                <Input id="timezone" {...form.register("timezone")} />
                {form.formState.errors.timezone ? (
                  <p className="text-sm text-destructive">
                    {form.formState.errors.timezone.message}
                  </p>
                ) : null}
              </div>
            </div>

            <div className="space-y-4">
              {people.fields.map((field, index) => (
                <div
                  key={field.id}
                  className="grid gap-4 rounded-3xl border bg-secondary/40 p-4 md:grid-cols-2"
                >
                  <div className="space-y-2">
                    <Label htmlFor={`people.${index}.name`}>
                      Person {index + 1} name{" "}
                      {index === 0 ? (
                        <span className="text-destructive">*</span>
                      ) : (
                        <span className="text-muted-foreground">(optional)</span>
                      )}
                    </Label>
                    <Input
                      id={`people.${index}.name`}
                      {...form.register(`people.${index}.name`)}
                    />
                    {form.formState.errors.people?.[index]?.name ? (
                      <p className="text-sm text-destructive">
                        {form.formState.errors.people[index]?.name?.message}
                      </p>
                    ) : null}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor={`people.${index}.email`}>
                      Person {index + 1} email{" "}
                      <span className="text-muted-foreground">(optional)</span>
                    </Label>
                    <Input
                      id={`people.${index}.email`}
                      type="email"
                      {...form.register(`people.${index}.email`)}
                    />
                    {form.formState.errors.people?.[index]?.email ? (
                      <p className="text-sm text-destructive">
                        {form.formState.errors.people[index]?.email?.message}
                      </p>
                    ) : null}
                  </div>
                </div>
              ))}

              {people.fields.length < 3 ? (
                <Button
                  type="button"
                  variant="outline"
                  className="rounded-3xl"
                  onClick={() => people.append({ name: "", email: "" })}
                >
                  <Plus className="mr-2 h-4 w-4" />
                  Add Person
                </Button>
              ) : null}
            </div>

            {onboardingMutation.isError ? (
              <p className="rounded-2xl bg-warning/15 p-3 text-sm text-warning-foreground">
                Onboarding failed. Check the API status and try again.
              </p>
            ) : null}

            <Button
              type="submit"
              className="rounded-3xl"
              disabled={onboardingMutation.isPending}
            >
              {onboardingMutation.isPending
                ? "Saving household..."
                : "Complete onboarding"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

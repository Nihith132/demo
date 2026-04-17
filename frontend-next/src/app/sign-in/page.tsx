"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Button, ButtonLink } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { apiFetch } from "@/lib/http";

type PatientAuthResponse = {
  access_token: string;
  token_type: string;
  patient_user_id: number;
};

export default function SignInPage() {
  const router = useRouter();

  const [mode, setMode] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // If already signed in as patient, go straight to intake.
    const t = localStorage.getItem("patient_token");
    if (t) router.replace("/patient/intake" as any);
  }, [router]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      if (mode === "login") {
        const body = new URLSearchParams();
        body.set("username", username);
        body.set("password", password);

        const res = await apiFetch<PatientAuthResponse>("/api/patient-auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body
        });

        localStorage.setItem("patient_token", res.access_token);
        localStorage.setItem("patient_user_id", String(res.patient_user_id));
        router.push("/patient/intake" as any);
      } else {
        const res = await apiFetch<PatientAuthResponse>("/api/patient-auth/register", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            username,
            password,
            display_name: username
          })
        });

        localStorage.setItem("patient_token", res.access_token);
        localStorage.setItem("patient_user_id", String(res.patient_user_id));
        router.push("/patient/intake" as any);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign-in failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto grid max-w-5xl gap-6 md:grid-cols-2 md:items-center">
      <div className="rounded-3xl border border-white/10 bg-gradient-to-br from-white/10 to-white/5 p-8">
        <div className="text-sm text-white/70">AI-powered healthcare triage</div>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight">Patient sign in</h1>
        <p className="mt-3 text-sm text-white/70">
          Sign in to upload reports, describe symptoms, and book an appointment.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <ButtonLink href="/doctor/login" variant="secondary">
            Are you a doctor?
          </ButtonLink>
          <ButtonLink href="/api-docs" variant="secondary">
            API docs
          </ButtonLink>
        </div>
      </div>

      <Card title={mode === "login" ? "Sign in" : "Create account"} desc="Username + password">
        <form onSubmit={onSubmit} className="grid gap-4">
          <Input label="Username" value={username} onChange={setUsername} placeholder="johndoe" />
          <Input label="Password" type="password" value={password} onChange={setPassword} placeholder="••••••••" />

          {error ? (
            <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-sm">{error}</div>
          ) : null}

          <Button type="submit" disabled={loading || !username || !password}>
            {loading ? "Please wait..." : mode === "login" ? "Sign in" : "Register"}
          </Button>

          <div className="text-sm text-white/70">
            {mode === "login" ? (
              <button
                type="button"
                onClick={() => setMode("register")}
                className="underline hover:text-white"
              >
                New patient? Register
              </button>
            ) : (
              <button
                type="button"
                onClick={() => setMode("login")}
                className="underline hover:text-white"
              >
                Already have an account? Sign in
              </button>
            )}
          </div>
        </form>
      </Card>
    </div>
  );
}

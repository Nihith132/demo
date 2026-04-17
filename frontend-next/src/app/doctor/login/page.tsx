"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";
import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { apiFetch } from "@/lib/http";

type LoginResponse = {
  access_token: string;
  token_type: string;
  doctor_id: number;
};

export default function DoctorLoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const body = new URLSearchParams();
      body.set("username", username);
      body.set("password", password);

      const res = await apiFetch<LoginResponse>("/api/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded"
        },
        body
      });

      localStorage.setItem("doctor_token", res.access_token);
      localStorage.setItem("doctor_id", String(res.doctor_id));
      router.push("/doctor" as any);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto grid max-w-5xl gap-6 md:grid-cols-2 md:items-center">
      <div className="rounded-3xl border border-white/10 bg-gradient-to-br from-white/10 to-white/5 p-8">
        <div className="text-sm text-white/70">Doctor portal</div>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight">Doctor sign in</h1>
        <p className="mt-3 text-sm text-white/70">
          Use your name (as stored in the doctor dataset) and password.
        </p>
        <div className="mt-6">
          <Link className="text-sm text-white/70 underline hover:text-white" href="/sign-in">
            Not a doctor? Go to patient sign in
          </Link>
        </div>
      </div>

      <Card title="Sign in" desc="Verify against doctor dataset">
        <form onSubmit={onSubmit} className="grid gap-4">
          <Input label="Doctor name" value={username} onChange={setUsername} placeholder="Dr. Priya Sharma" />
          <Input label="Password" type="password" value={password} onChange={setPassword} placeholder="••••••••" />

          {error ? <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-sm">{error}</div> : null}

          <Button type="submit" disabled={loading || !username || !password}>
            {loading ? "Signing in..." : "Sign in"}
          </Button>
        </form>
      </Card>
    </div>
  );
}

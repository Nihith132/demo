"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/Button";
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
      router.push("/doctor");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-md">
      <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
        <h1 className="text-xl font-semibold">Doctor login</h1>
        <p className="mt-2 text-sm text-white/70">
          Username is the doctor name (e.g. <span className="text-white">Dr. Priya Sharma</span>).
        </p>

        <form onSubmit={onSubmit} className="mt-6 grid gap-4">
          <Input label="Doctor name" value={username} onChange={setUsername} placeholder="Dr. Priya Sharma" />
          <Input label="Password" type="password" value={password} onChange={setPassword} placeholder="password" />

          {error ? <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-sm">{error}</div> : null}

          <Button type="submit" disabled={loading || !username || !password}>
            {loading ? "Signing in..." : "Sign in"}
          </Button>
        </form>
      </div>
    </div>
  );
}

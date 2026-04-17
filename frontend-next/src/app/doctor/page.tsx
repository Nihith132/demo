"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";

import { ButtonLink } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { apiFetch } from "@/lib/http";

type SBAR = {
  situation: string;
  background: string;
  assessment: string;
  recommendation: string;
};

type DoctorPatientCard = {
  patient_id: string;
  patient_name?: string | null;
  age?: number | null;
  department?: string | null;
  scheduled_time: string;
  severity_score?: number | null;
  severity_reasoning?: string | null;
  ai_status: string;
  sbar?: SBAR | null;
  prerequisites: string[];
  ocr_required: boolean;
};

type Analytics = {
  doctor_id: number;
  total_booked: number;
  ai_ready: number;
  ai_processing: number;
  ai_error: number;
  ocr_required: number;
  severity_counts: Record<string, number>;
};

export default function DoctorDashboardPage() {
  const [token, setToken] = useState<string | null>(null);
  const [cards, setCards] = useState<DoctorPatientCard[]>([]);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setToken(localStorage.getItem("doctor_token"));
  }, []);

  const isAuthed = useMemo(() => Boolean(token), [token]);

  async function load() {
    if (!token) return;
    setError(null);
    try {
      const [c, a] = await Promise.all([
        apiFetch<DoctorPatientCard[]>("/api/doctors/dashboard", { token }),
        apiFetch<Analytics>("/api/doctors/analytics", { token })
      ]);
      setCards(c);
      setAnalytics(a);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    }
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  if (!isAuthed) {
    return (
      <div className="mx-auto max-w-xl">
        <Card title="Doctor dashboard" desc="Login required">
          <div className="flex items-center gap-3">
            <ButtonLink href="/doctor/login">Go to login</ButtonLink>
            <Link className="text-sm text-white/70 underline" href="/">
              Back
            </Link>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="grid gap-6">
      <div className="grid gap-4 md:grid-cols-3">
        <Card title="Booked" desc="Total booked appointments">
          <div className="text-3xl font-semibold">{analytics?.total_booked ?? "—"}</div>
        </Card>
        <Card title="AI status" desc="Ready / Processing / Error">
          <div className="text-sm text-white/70">
            <div>Ready: {analytics?.ai_ready ?? "—"}</div>
            <div>Processing: {analytics?.ai_processing ?? "—"}</div>
            <div>Error: {analytics?.ai_error ?? "—"}</div>
          </div>
        </Card>
        <Card title="OCR flags" desc="Uploads likely requiring OCR">
          <div className="text-3xl font-semibold">{analytics?.ocr_required ?? "—"}</div>
        </Card>
      </div>

      {error ? <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-sm">{error}</div> : null}

      <div className="grid gap-4">
        <h2 className="text-lg font-semibold">Patients</h2>
        {cards.length === 0 ? (
          <div className="rounded-2xl border border-white/10 bg-white/5 p-6 text-sm text-white/70">
            No booked patients yet.
          </div>
        ) : (
          <div className="grid gap-3">
            {cards.map((c) => (
              <Link
                key={c.patient_id}
                href={`/doctor/patient/${c.patient_id}`}
                className="rounded-2xl border border-white/10 bg-white/5 p-5 hover:bg-white/10 transition"
              >
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div className="font-medium">{c.patient_name || "Unnamed"}</div>
                    <div className="mt-1 text-sm text-white/70">
                      {c.department || "—"} • Severity {c.severity_score ?? "—"} • AI {c.ai_status}
                      {c.ocr_required ? " • OCR" : ""}
                    </div>
                  </div>
                  <div className="text-sm text-white/70">{new Date(c.scheduled_time).toLocaleString()}</div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

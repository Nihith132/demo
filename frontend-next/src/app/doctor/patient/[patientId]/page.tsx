"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";

import { Button, ButtonLink } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { apiFetch } from "@/lib/http";

type SBAR = {
  situation: string;
  background: string;
  assessment: string;
  recommendation: string;
};

type DoctorPatientDetail = {
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

export default function DoctorPatientDetailPage() {
  const router = useRouter();
  const params = useParams<{ patientId: string }>();
  const patientId = params.patientId;

  const [token, setToken] = useState<string | null>(null);
  const [data, setData] = useState<DoctorPatientDetail | null>(null);
  const [prereq, setPrereq] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setToken(localStorage.getItem("doctor_token"));
  }, []);

  async function load() {
    if (!token) return;
    setError(null);
    try {
      const d = await apiFetch<DoctorPatientDetail>(`/api/doctors/patient/${patientId}`, { token });
      setData(d);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    }
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, patientId]);

  async function addPrerequisite() {
    if (!token || !prereq.trim()) return;
    setError(null);
    try {
      await apiFetch<{ status: string }>("/api/doctors/action", {
        method: "POST",
        token,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ patient_id: patientId, prerequisite: prereq.trim() })
      });
      setPrereq("");
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to add prerequisite");
    }
  }

  if (!token) {
    return (
      <div className="mx-auto max-w-xl">
        <Card title="Doctor patient view" desc="Login required">
          <ButtonLink href="/doctor/login">Go to login</ButtonLink>
        </Card>
      </div>
    );
  }

  return (
    <div className="grid gap-6">
      <div className="flex items-center justify-between gap-3">
        <ButtonLink href="/doctor" variant="secondary">
          Back
        </ButtonLink>
        <Button variant="secondary" onClick={() => router.refresh()}>
          Refresh
        </Button>
      </div>

      {error ? <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-sm">{error}</div> : null}

      <Card title={data?.patient_name || "Patient"} desc={`${data?.department || "—"} • AI ${data?.ai_status || "—"}`}>
        <div className="grid gap-4">
          <div className="grid gap-2 text-sm text-white/70">
            <div>Severity: {data?.severity_score ?? "—"}</div>
            <div>Scheduled: {data ? new Date(data.scheduled_time).toLocaleString() : "—"}</div>
            <div>OCR required: {data?.ocr_required ? "Yes" : "No"}</div>
          </div>

          <div className="grid gap-2">
            <div className="text-sm font-medium">SBAR</div>
            <div className="grid gap-2 text-sm text-white/70">
              <div><span className="text-white">S:</span> {data?.sbar?.situation || "—"}</div>
              <div><span className="text-white">B:</span> {data?.sbar?.background || "—"}</div>
              <div><span className="text-white">A:</span> {data?.sbar?.assessment || "—"}</div>
              <div><span className="text-white">R:</span> {data?.sbar?.recommendation || "—"}</div>
            </div>
          </div>

          <div className="grid gap-2">
            <div className="text-sm font-medium">Severity reasoning</div>
            <div className="rounded-xl border border-white/10 bg-black/20 p-3 text-sm text-white/70">
              {data?.severity_reasoning || "—"}
            </div>
          </div>

          <div className="grid gap-2">
            <div className="text-sm font-medium">Prerequisites</div>
            <div className="flex flex-wrap gap-2">
              {(data?.prerequisites || []).map((p) => (
                <span key={p} className="rounded-full border border-white/10 bg-white/10 px-3 py-1 text-xs">
                  {p}
                </span>
              ))}
            </div>

            <div className="mt-2 grid gap-2 md:grid-cols-[1fr_auto]">
              <Input label="Add prerequisite" value={prereq} onChange={setPrereq} placeholder="e.g. Chest X-Ray" />
              <div className="self-end">
                <Button onClick={addPrerequisite} disabled={!prereq.trim()}>
                  Add
                </Button>
              </div>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}

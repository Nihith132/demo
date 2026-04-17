"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input, Textarea } from "@/components/ui/Input";
import { apiFetch } from "@/lib/http";

type HistoryRow = {
  patient_id: string;
  patient_name: string | null;
  age: number | null;
  department: string | null;
  status: string;
  ai_status: string;
  severity_score: number | null;
  created_at: string;
};

type SubmitResponse = {
  patient_id: string;
  status: string;
  message: string;
};

type Doctor = {
  id: number;
  name: string;
  department: string;
  current_load: number;
  is_available: boolean;
};

type BookResponse = {
  patient_id: string;
  appointment_id: number;
  status: string;
  message: string;
};

export default function PatientIntakePage() {
  const router = useRouter();

  const [token, setToken] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoryRow[]>([]);
  const [error, setError] = useState<string | null>(null);

  // intake form
  const [name, setName] = useState("");
  const [age, setAge] = useState("30");
  const [desc, setDesc] = useState("");
  const [pdf, setPdf] = useState<File | null>(null);

  // booking
  const [activePatientId, setActivePatientId] = useState<string | null>(null);
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [scheduledTime, setScheduledTime] = useState("");
  const [selectedDoctor, setSelectedDoctor] = useState<string>("");

  const readyToBook = useMemo(
    () => Boolean(activePatientId && scheduledTime && selectedDoctor),
    [activePatientId, scheduledTime, selectedDoctor]
  );

  const authed = useMemo(() => Boolean(token), [token]);

  useEffect(() => {
    const t = localStorage.getItem("patient_token");
    if (!t) {
      router.replace("/sign-in" as any);
      return;
    }
    setToken(t);
    void loadHistory(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function loadHistory(activeToken: string) {
    setError(null);
    try {
      const rows = await apiFetch<HistoryRow[]>("/api/patient/history", { token: activeToken });
      setHistory(rows);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load history");
    }
  }

  async function signOut() {
    localStorage.removeItem("patient_token");
    localStorage.removeItem("patient_user_id");
    router.push("/sign-in" as any);
  }

  async function submitIntake() {
    setError(null);
    if (!pdf) {
      setError("Please select a PDF");
      return;
    }

    if (!token) {
      setError("Please sign in first");
      return;
    }

    try {
      const form = new FormData();
      form.append("patient_name", name);
      form.append("age", age);
      form.append("description", desc);
      form.append("pdf", pdf);

      const res = await apiFetch<SubmitResponse>("/api/patient/submit", {
        method: "POST",
        token,
        body: form
      });

      setActivePatientId(res.patient_id);
      await loadHistory(token);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Submit failed");
    }
  }

  async function loadDoctors() {
    setError(null);
    if (!activePatientId || !token) return;
    try {
      const rows = await apiFetch<Doctor[]>(`/api/patient/doctors?patient_id=${activePatientId}`, { token });
      setDoctors(rows);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load doctors");
    }
  }

  async function book() {
    if (!readyToBook || !activePatientId || !token) return;
    setError(null);
    try {
      const payload = {
        patient_id: activePatientId,
        doctor_id: Number(selectedDoctor),
        scheduled_time: new Date(scheduledTime).toISOString()
      };

      const res = await apiFetch<BookResponse>("/api/patient/book", {
        method: "POST",
        token,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      await loadHistory(token);
      return res;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Booking failed");
    }
  }

  if (!authed) {
    return null;
  }

  return (
    <div className="grid gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold">Patient intake</h1>
          <p className="mt-1 text-sm text-white/70">Upload a report and describe symptoms.</p>
        </div>
        <Button variant="secondary" onClick={signOut}>
          Sign out
        </Button>
      </div>

      {error ? <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-sm">{error}</div> : null}

      <div className="grid gap-4 md:grid-cols-2">
        <Card title="New case" desc="PDF + symptoms">
          <div className="grid gap-3">
            <Input label="Full name" value={name} onChange={setName} placeholder="John Doe" />
            <Input label="Age" type="number" value={age} onChange={setAge} />
            <Textarea label="Symptoms" value={desc} onChange={setDesc} placeholder="Describe your symptoms..." />

            <label className="grid gap-1 text-sm">
              <span className="text-white/70">PDF report</span>
              <input
                type="file"
                accept="application/pdf"
                onChange={(e) => setPdf(e.target.files?.[0] || null)}
                className="rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm"
              />
            </label>

            <Button onClick={submitIntake}>
              Submit intake
            </Button>

            {activePatientId ? (
              <div className="rounded-xl border border-white/10 bg-black/20 p-3 text-sm text-white/70">
                Active case: <span className="text-white">{activePatientId}</span>
              </div>
            ) : null}
          </div>
        </Card>

        <Card title="Booking" desc="Choose a doctor for the active case">
          <div className="grid gap-3">
            <Button variant="secondary" onClick={loadDoctors} disabled={!activePatientId}>
              Load doctors
            </Button>

            <label className="grid gap-1 text-sm">
              <span className="text-white/70">Select doctor</span>
              <select
                value={selectedDoctor}
                onChange={(e) => setSelectedDoctor(e.target.value)}
                className="rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm"
              >
                <option value="">—</option>
                {doctors.map((d) => (
                  <option key={d.id} value={String(d.id)}>
                    {d.name} ({d.department})
                  </option>
                ))}
              </select>
            </label>

            <Input label="Scheduled time" type="datetime-local" value={scheduledTime} onChange={setScheduledTime} />

            <Button onClick={book} disabled={!readyToBook}>
              Book appointment
            </Button>
          </div>
        </Card>
      </div>

      <Card title="History" desc="Your previous intakes">
        {history.length === 0 ? (
          <div className="text-sm text-white/70">No history yet.</div>
        ) : (
          <div className="grid gap-2">
            {history.map((h) => (
              <div key={h.patient_id} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div className="font-medium">{h.patient_name || "Unnamed"}</div>
                    <div className="mt-1 text-sm text-white/70">
                      {h.department || "—"} • status {h.status} • AI {h.ai_status} • severity {h.severity_score ?? "—"}
                    </div>
                  </div>
                  <div className="text-sm text-white/70">{new Date(h.created_at).toLocaleString()}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}

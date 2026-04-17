import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { ButtonLink } from "@/components/ui/Button";

export default function HomePage() {
  return (
    <div className="mx-auto grid max-w-5xl gap-6 md:grid-cols-2 md:items-center">
      <div className="rounded-3xl border border-white/10 bg-gradient-to-br from-white/10 to-white/5 p-8">
        <div className="text-sm text-white/70">AI-powered healthcare triage</div>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight">Welcome</h1>
        <p className="mt-3 text-sm text-white/70">
          Sign in to start a new intake, upload PDFs, and book appointments.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <ButtonLink href="/sign-in">Patient sign in</ButtonLink>
          <ButtonLink href="/api-docs" variant="secondary">
            API docs
          </ButtonLink>
        </div>
      </div>

      <Card title="How it works" desc="Patient → triage → booking → doctor dashboard">
        <ul className="list-disc pl-5 text-sm text-white/70">
          <li>Upload a PDF report and describe symptoms</li>
          <li>System routes to a department</li>
          <li>Book an appointment with an available doctor</li>
          <li>Doctors review SBAR + severity and add prerequisites</li>
        </ul>
      </Card>
    </div>
  );
}

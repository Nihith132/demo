import Link from "next/link";
import { Card } from "@/components/ui/Card";
import { ButtonLink } from "@/components/ui/Button";

export default function HomePage() {
  return (
    <div className="grid gap-6">
      <div className="rounded-2xl border border-white/10 bg-white/5 p-6">
        <h1 className="text-2xl font-semibold">AI4 Healthcare Triage (MVP)</h1>
        <p className="mt-2 text-sm text-white/70">
          Patient intake → department routing → booking → doctor dashboard with SBAR/severity.
        </p>

        <div className="mt-6 flex flex-wrap gap-3">
          <ButtonLink href="/patient">Patient dashboard</ButtonLink>
          <ButtonLink href="/doctor/login" variant="secondary">
            Doctor login
          </ButtonLink>
          <Link className="text-sm text-white/70 underline" href="/api-docs">
            API docs (backend)
          </Link>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card title="Patient flow" desc="Uses Firebase Auth token (Google sign-in) and calls /api/patient/*">
          <ul className="list-disc pl-5 text-sm text-white/70">
            <li>Sign in with Google (Firebase)</li>
            <li>View history</li>
            <li>Upload PDF + describe symptoms</li>
            <li>Book a doctor</li>
          </ul>
        </Card>
        <Card title="Doctor flow" desc="Uses backend JWT and calls /api/doctors/*">
          <ul className="list-disc pl-5 text-sm text-white/70">
            <li>Login with doctor name + password</li>
            <li>View patient cards</li>
            <li>See analytics</li>
            <li>Add prerequisites</li>
          </ul>
        </Card>
      </div>
    </div>
  );
}

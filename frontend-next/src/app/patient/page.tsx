"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function PatientLegacyPage() {
  const router = useRouter();
  useEffect(() => {
    const t = localStorage.getItem("patient_token");
    router.replace((t ? "/patient/intake" : "/sign-in") as any);
  }, [router]);
  return null;
}

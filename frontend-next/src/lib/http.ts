import { BACKEND_URL } from "@/lib/config";

export async function apiFetch<T>(
  path: string,
  opts: {
    method?: string;
    headers?: Record<string, string>;
    body?: BodyInit | null;
    token?: string;
  } = {}
): Promise<T> {
  const headers: Record<string, string> = {
    ...(opts.headers || {})
  };

  if (opts.token) {
    headers["Authorization"] = `Bearer ${opts.token}`;
  }

  const res = await fetch(`${BACKEND_URL}${path}`, {
    method: opts.method || "GET",
    headers,
    body: opts.body ?? null
  });

  if (!res.ok) {
    let detail = "Request failed";
    try {
      const data = await res.json();
      detail = data.detail || JSON.stringify(data);
    } catch {
      detail = await res.text();
    }
    throw new Error(detail);
  }

  return (await res.json()) as T;
}

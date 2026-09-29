/**
 * Minimal typed HTTP client.
 * - In the browser we call "/api/*", which next.config.ts proxies to the backend.
 * - On the server (RSC / route handlers) we call the backend directly via API_URL.
 */

const BASE_URL =
  typeof window === "undefined" ? (process.env.API_URL ?? "http://localhost:8000") : "/api";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
    public readonly body?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body && !(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers,
    credentials: "include",
    cache: "no-store",
  });

  const body: unknown = res.status === 204 ? null : await res.json().catch(() => null);

  if (!res.ok) {
    const detail =
      body && typeof body === "object" && "detail" in body ? String(body.detail) : res.statusText;
    throw new ApiError(res.status, detail, body);
  }
  return body as T;
}

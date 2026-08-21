import type { TokenResponse } from "@/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function readStoredToken() {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem("access_token");
}

function writeStoredToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) sessionStorage.setItem("access_token", token);
  else sessionStorage.removeItem("access_token");
}

let accessToken: string | null = null;
let refreshPromise: Promise<boolean> | null = null;

export function setAccessToken(token: string | null) {
  accessToken = token;
  writeStoredToken(token);
}

export function getAccessToken() {
  if (!accessToken) accessToken = readStoredToken();
  return accessToken;
}

function detailMessage(detail: unknown) {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => (typeof item === "object" && item && "msg" in item ? String(item.msg) : String(item)))
      .join(", ");
  }
  return "Request failed";
}

async function tryRefresh() {
  const response = await fetch(`${API_URL}/api/v1/auth/refresh`, {
    method: "POST",
    credentials: "include",
  });
  if (!response.ok) {
    setAccessToken(null);
    return false;
  }
  const data = (await response.json()) as TokenResponse;
  setAccessToken(data.access_token);
  return true;
}

export async function api<T>(path: string, options: RequestInit = {}, retry = true): Promise<T> {
  const headers = new Headers(options.headers);
  if (!(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const token = getAccessToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(`${API_URL}${path}`, {
    cache: "no-store",
    ...options,
    headers,
    credentials: "include",
  });

  const isAuthPath = path.startsWith("/api/v1/auth/login") || path.startsWith("/api/v1/auth/register");
  if (response.status === 401 && retry && !isAuthPath) {
    if (!refreshPromise) {
      refreshPromise = tryRefresh().finally(() => {
        refreshPromise = null;
      });
    }
    const refreshed = await refreshPromise;
    if (refreshed) return api<T>(path, options, false);
  }

  if (response.status === 204) return undefined as T;

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(detailMessage((data as { detail?: unknown }).detail));
  }
  return data as T;
}

export const authApi = {
  register: (body: { email: string; password: string; name: string }) =>
    api<TokenResponse>("/api/v1/auth/register", { method: "POST", body: JSON.stringify(body) }),
  login: (body: { email: string; password: string }) =>
    api<TokenResponse>("/api/v1/auth/login", { method: "POST", body: JSON.stringify(body) }),
  refresh: () => api<TokenResponse>("/api/v1/auth/refresh", { method: "POST" }),
  logout: () => api<void>("/api/v1/auth/logout", { method: "POST" }),
  me: () => api<TokenResponse["user"]>("/api/v1/auth/me"),
};

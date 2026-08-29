/**
 * OS Privacidad — Lib Package
 * Utilidades compartidas del frontend.
 */

/** URL base de la API */
export const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

/**
 * Fetch wrapper con manejo de errores estándar de la API.
 */
export async function apiFetch<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    credentials: "include", // Para enviar cookies httpOnly (refresh token)
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const message =
      body?.error?.message || `Error ${res.status}: ${res.statusText}`;
    throw new Error(message);
  }

  return res.json();
}

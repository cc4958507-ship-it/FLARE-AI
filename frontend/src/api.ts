import { msg } from './i18n';
export async function api<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch("/api/v1" + path, {
    method: body === undefined ? "GET" : "POST",
    headers:
      body === undefined ? undefined : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) {
    let message = msg('Request failed ({0}). Please retry.', [response.status]);
    try {
      const error = await response.json();
      message = typeof error.detail === "string" ? error.detail : message;
    } catch {
      /* Preserve the HTTP error for non-JSON responses. */
    }
    throw new Error(message);
  }
  return response.json();
}

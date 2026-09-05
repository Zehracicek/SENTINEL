/** Yazma uçları için paylaşılan istek yardımcısı.

Tarayıcıda `VITE_API_TOKEN` (Vite derleme zamanı) `X-API-Token` başlığına
yazılır. Anahtar yoksa istek yine gider; sunucu 401/503 döner — UI bunu
göstermek zorundadır, yoksa düğmeler sessizce ölür.
*/

export function apiUrl(path) {
  const base = String(import.meta.env.VITE_API_BASE || "").replace(/\/$/, "");
  const p = String(path || "").startsWith("/") ? path : `/${path}`;
  return `${base}${p}`;
}

export function apiToken() {
  return String(import.meta.env.VITE_API_TOKEN || "").trim();
}

export function hasApiToken() {
  return apiToken().length > 0;
}

export function writeAuthHint() {
  if (hasApiToken()) return null;
  return (
    "Yazma uçları X-API-Token ister. frontend/.env içine VITE_API_TOKEN " +
    "yazıp Vite'i yeniden başlatın (değer backend SENTINEL_API_TOKEN ile aynı olmalı)."
  );
}

export async function apiFetch(url, options = {}) {
  const headers = new Headers(options.headers || {});
  const token = apiToken();
  if (token) {
    headers.set("X-API-Token", token);
  }

  const res = await fetch(apiUrl(url), { ...options, headers });
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      if (typeof body?.detail === "string") {
        detail = body.detail;
      } else if (body?.detail != null) {
        detail = JSON.stringify(body.detail);
      }
    } catch {
      /* gövde JSON değil */
    }
    const err = new Error(detail);
    err.status = res.status;
    throw err;
  }

  if (res.status === 204) return null;
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) return res.json();
  return res;
}

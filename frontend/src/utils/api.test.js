import { afterEach, describe, expect, it, vi } from "vitest";

import { apiFetch, apiToken, hasApiToken, writeAuthHint } from "./api";

describe("api token helpers", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.unstubAllGlobals();
  });

  it("token yokken başlık eklemez ve ipucu döner", async () => {
    vi.stubEnv("VITE_API_TOKEN", "");
    expect(hasApiToken()).toBe(false);
    expect(writeAuthHint()).toMatch(/VITE_API_TOKEN/);

    const fetchMock = vi.fn(async (_url, opts) => {
      const headers = new Headers(opts.headers);
      expect(headers.has("X-API-Token")).toBe(false);
      return new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    });
    vi.stubGlobal("fetch", fetchMock);

    await apiFetch("/api/x", { method: "PATCH" });
    expect(fetchMock).toHaveBeenCalledOnce();
  });

  it("token varken X-API-Token yazar", async () => {
    vi.stubEnv("VITE_API_TOKEN", "secret-token");
    expect(apiToken()).toBe("secret-token");
    expect(hasApiToken()).toBe(true);
    expect(writeAuthHint()).toBeNull();

    const fetchMock = vi.fn(async (_url, opts) => {
      const headers = new Headers(opts.headers);
      expect(headers.get("X-API-Token")).toBe("secret-token");
      return new Response(JSON.stringify({ enabled: true }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    });
    vi.stubGlobal("fetch", fetchMock);

    const body = await apiFetch("/api/settings/rover-thinking", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enabled: true }),
    });
    expect(body).toEqual({ enabled: true });
  });

  it("401 gövdesindeki detail'i Error.message yapar", async () => {
    vi.stubEnv("VITE_API_TOKEN", "");
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(JSON.stringify({ detail: "Geçersiz veya eksik X-API-Token başlığı." }), {
          status: 401,
          headers: { "Content-Type": "application/json" },
        })
      )
    );

    await expect(apiFetch("/api/anomalies/1/acknowledge", { method: "PATCH" })).rejects.toThrow(
      /X-API-Token/
    );
  });
});

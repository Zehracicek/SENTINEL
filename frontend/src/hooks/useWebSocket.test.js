/**
 * useWebSocket testleri.
 *
 * Buradaki senaryolar daha önce gerçek hatalara yol açan durumları kilitler:
 *  - aynı anda birden fazla soket açılması,
 *  - kapanan eski bir soketin ikinci bir yeniden bağlanma döngüsü başlatması,
 *  - React akışa yetişemediğinde mesaj kuyruğunun sınırsız büyümesi.
 */

import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import useWebSocket from "./useWebSocket";

const URL = "ws://localhost:8000/ws/live-feed";

let sockets = [];

class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  constructor(url) {
    this.url = url;
    this.readyState = MockWebSocket.CONNECTING;
    this.sent = [];
    this.onopen = null;
    this.onmessage = null;
    this.onclose = null;
    this.onerror = null;
    sockets.push(this);
  }

  open() {
    this.readyState = MockWebSocket.OPEN;
    this.onopen?.();
  }

  receive(payload) {
    this.onmessage?.({ data: JSON.stringify(payload) });
  }

  receiveRaw(data) {
    this.onmessage?.({ data });
  }

  close() {
    this.readyState = MockWebSocket.CLOSED;
    this.onclose?.();
  }

  send(data) {
    this.sent.push(data);
  }
}

beforeEach(() => {
  sockets = [];
  vi.useFakeTimers();
  vi.stubGlobal("WebSocket", MockWebSocket);
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe("bağlantı yaşam döngüsü", () => {
  it("url yokken soket açmaz", () => {
    const { result } = renderHook(() => useWebSocket(""));
    expect(sockets).toHaveLength(0);
    expect(result.current.status).toBe("disconnected");
  });

  it("tek bir soket açar ve açılınca connected olur", () => {
    const { result } = renderHook(() => useWebSocket(URL));

    expect(sockets).toHaveLength(1);
    expect(result.current.status).toBe("connecting");

    act(() => sockets[0].open());

    expect(result.current.status).toBe("connected");
  });

  it("kapanınca gecikmeyle yeniden bağlanır", () => {
    renderHook(() => useWebSocket(URL));
    act(() => sockets[0].open());

    act(() => sockets[0].close());
    expect(sockets).toHaveLength(1); // henüz beklemede

    act(() => vi.advanceTimersByTime(3000));
    expect(sockets).toHaveLength(2);
  });

  it("eski bir soketin geç gelen onclose'u ikinci döngü başlatmaz", () => {
    renderHook(() => useWebSocket(URL));
    const first = sockets[0];
    act(() => first.open());

    act(() => first.close());
    act(() => vi.advanceTimersByTime(3000));
    expect(sockets).toHaveLength(2);

    // Artık geçersiz olan ilk soket tekrar onclose tetiklerse yok sayılmalı
    act(() => first.onclose?.());
    act(() => vi.advanceTimersByTime(3000));

    expect(sockets).toHaveLength(2);
  });

  it("unmount sonrası yeniden bağlanmaz", () => {
    const { unmount } = renderHook(() => useWebSocket(URL));
    act(() => sockets[0].open());

    unmount();
    act(() => vi.advanceTimersByTime(10000));

    expect(sockets).toHaveLength(1);
  });
});

describe("mesaj kuyruğu", () => {
  it("gelen mesajları batch olarak toplar", async () => {
    const { result } = renderHook(() => useWebSocket(URL));
    act(() => sockets[0].open());

    await act(async () => {
      sockets[0].receive({ type: "stats_update", data: { a: 1 } });
      sockets[0].receive({ type: "sensor_reading", data: { b: 2 } });
    });

    expect(result.current.messageBatch.items).toHaveLength(2);
    expect(result.current.messageBatch.items[0].type).toBe("stats_update");
  });

  it("kuyruk 500 mesajı aşmaz ve en yenileri tutar", async () => {
    const { result } = renderHook(() => useWebSocket(URL));
    act(() => sockets[0].open());

    await act(async () => {
      for (let i = 0; i < 700; i += 1) {
        sockets[0].receive({ type: "sensor_reading", seq: i });
      }
    });

    const { items } = result.current.messageBatch;
    expect(items).toHaveLength(500);
    // En yeniler korunmalı: 200..699
    expect(items[0].seq).toBe(200);
    expect(items[items.length - 1].seq).toBe(699);
  });

  it("bozuk JSON bağlantıyı düşürmez", async () => {
    const { result } = renderHook(() => useWebSocket(URL));
    act(() => sockets[0].open());

    await act(async () => {
      sockets[0].receiveRaw("{bu gecerli json degil");
      sockets[0].receive({ type: "stats_update", data: { ok: true } });
    });

    expect(result.current.status).toBe("connected");
    expect(result.current.messageBatch.items).toHaveLength(1);
  });

  it("her batch artan bir seq numarası taşır", async () => {
    const { result } = renderHook(() => useWebSocket(URL));
    act(() => sockets[0].open());

    await act(async () => sockets[0].receive({ type: "stats_update" }));
    const first = result.current.messageBatch.seq;

    await act(async () => sockets[0].receive({ type: "stats_update" }));

    expect(result.current.messageBatch.seq).toBe(first + 1);
  });
});

describe("send", () => {
  it("soket açıkken gönderir", () => {
    const { result } = renderHook(() => useWebSocket(URL));
    act(() => sockets[0].open());

    act(() => result.current.send({ ping: 1 }));

    expect(sockets[0].sent).toEqual(['{"ping":1}']);
  });

  it("soket açık değilken sessizce yok sayar", () => {
    const { result } = renderHook(() => useWebSocket(URL));

    act(() => result.current.send({ ping: 1 }));

    expect(sockets[0].sent).toEqual([]);
  });
});

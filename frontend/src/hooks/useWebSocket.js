import { useCallback, useEffect, useRef, useState } from "react";

const RECONNECT_DELAY = 3000;
const MAX_QUEUED_MESSAGES = 500;

/** Sunucunun gönderebileceği genişletilmiş tipler; kuyrukta tutulur, işlenmesi useAnomalyData.js içindedir. */
export const DASHBOARD_WS_TYPES = new Set([
  "orbiter_stats",
  "model_update",
  "energy_stats",
  "rl_stats",
  "stats_update",
  "uplink_queue_update",
  "sensor_reading",
  "anomaly_alert",
  "rover_thinking",
]);

export default function useWebSocket(url) {
  const [status, setStatus] = useState("disconnected");
  const [messageBatch, setMessageBatch] = useState(null);
  const wsRef = useRef(null);
  const reconnectTimer = useRef(null);
  const mountedRef = useRef(true);
  const queueRef = useRef([]);
  const flushScheduledRef = useRef(false);
  const seqRef = useRef(0);

  const flushQueue = useCallback(() => {
    flushScheduledRef.current = false;
    if (!mountedRef.current) return;
    const items = queueRef.current;
    queueRef.current = [];
    if (items.length === 0) return;
    seqRef.current += 1;
    setMessageBatch({ seq: seqRef.current, items });
  }, []);

  const connect = useCallback(() => {
    const existing = wsRef.current;
    // OPEN veya CONNECTING bir soket varsa yeni bağlantı açmayalım; aksi halde
    // önceki soket kapatılmadan referansı ezilir ve arkada açık kalır.
    if (
      existing &&
      (existing.readyState === WebSocket.OPEN ||
        existing.readyState === WebSocket.CONNECTING)
    ) {
      return;
    }
    if (existing && existing.readyState === WebSocket.CLOSING) {
      existing.onclose = null;
      existing.onerror = null;
      existing.onmessage = null;
    }

    setStatus("connecting");
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      if (mountedRef.current) setStatus("connected");
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (import.meta.env?.DEV && data?.type && !DASHBOARD_WS_TYPES.has(data.type)) {
          console.warn("[ws] bilinmeyen mesaj tipi:", data.type);
        }
        queueRef.current.push(data);
        // React akışa yetişemezse kuyruk sınırsız büyümesin; en yenileri tut.
        if (queueRef.current.length > MAX_QUEUED_MESSAGES) {
          queueRef.current = queueRef.current.slice(-MAX_QUEUED_MESSAGES);
        }
        if (!flushScheduledRef.current) {
          flushScheduledRef.current = true;
          queueMicrotask(flushQueue);
        }
      } catch {
        /* ignore malformed JSON */
      }
    };

    ws.onclose = () => {
      // Yalnızca güncel soketin kapanışı yeniden bağlanmayı tetiklesin;
      // eski bir soketin geç gelen onclose'u ikinci bir döngü başlatmasın.
      if (!mountedRef.current || wsRef.current !== ws) return;
      setStatus("disconnected");
      clearTimeout(reconnectTimer.current);
      reconnectTimer.current = setTimeout(() => {
        if (mountedRef.current) connect();
      }, RECONNECT_DELAY);
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [url, flushQueue]);

  useEffect(() => {
    mountedRef.current = true;
    connect();
    return () => {
      mountedRef.current = false;
      clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  const send = useCallback((data) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(typeof data === "string" ? data : JSON.stringify(data));
    }
  }, []);

  return { status, messageBatch, send };
}

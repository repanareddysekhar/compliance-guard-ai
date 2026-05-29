import { useState, useEffect } from 'react';
import { WsEvent, ScanStatus } from '../types';

export function useScanWebSocket(scanId: string | null) {
  const [events, setEvents] = useState<WsEvent[]>([]);
  const [status, setStatus] = useState<ScanStatus>("PENDING");

  useEffect(() => {
    setEvents([]);
    setStatus(scanId ? "RUNNING" : "PENDING");
    if (!scanId) return;

    const wsUrl = `ws://localhost:8000/ws/scan-status?scan_id=${scanId}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setStatus("RUNNING");
    };

    ws.onmessage = (msg) => {
      const event = JSON.parse(msg.data) as WsEvent;
      setEvents((prev: WsEvent[]) => [...prev, event]);
      
      if (event.type === "SCAN_COMPLETED") setStatus("COMPLETED");
      if (event.type === "SCAN_FAILED") setStatus("FAILED");
      if (event.type === "SCAN_STARTED") setStatus("RUNNING");
    };

    ws.onerror = (err) => {
      console.error("WebSocket error:", err);
    };

    return () => ws.close();
  }, [scanId]);

  return { events, status };
}

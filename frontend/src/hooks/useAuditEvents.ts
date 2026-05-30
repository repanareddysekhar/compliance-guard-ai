import { useEffect, useState } from 'react';
import client from '../api/client';
import { AuditEvent } from '../types';

export function useAuditEvents(scanId?: string) {
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!scanId) {
      setAuditEvents([]);
      setError(null);
      setLoading(false);
      return;
    }

    let cancelled = false;
    let intervalId: number | undefined;

    async function fetchAuditEvents() {
      setLoading(true);
      try {
        const response = await client.get<AuditEvent[]>(`/api/audit/${scanId}`);
        if (!cancelled) {
          setAuditEvents(response.data);
          setError(null);
        }
      } catch (err: unknown) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to fetch audit events');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchAuditEvents();
    intervalId = window.setInterval(fetchAuditEvents, 1500);

    return () => {
      cancelled = true;
      if (intervalId) {
        window.clearInterval(intervalId);
      }
    };
  }, [scanId]);

  return { auditEvents, loading, error };
}

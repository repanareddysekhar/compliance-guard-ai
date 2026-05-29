import { useState, useEffect } from 'react';
import client from '../api/client';
import { Violation } from '../types';

export function useViolations(scanId?: string) {
  const [violations, setViolations] = useState<Violation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!scanId) {
      setViolations([]);
      setError(null);
      setLoading(false);
      return;
    }

    let cancelled = false;
    let intervalId: number | undefined;

    async function fetchViolations() {
      setLoading(true);
      try {
        const response = await client.get('/api/violations', {
          params: { scan_id: scanId }
        });
        if (!cancelled) {
          setViolations(response.data);
          setError(null);
        }
      } catch (err: unknown) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to fetch violations');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    fetchViolations();
    intervalId = window.setInterval(fetchViolations, 1500);

    return () => {
      cancelled = true;
      if (intervalId) {
        window.clearInterval(intervalId);
      }
    };
  }, [scanId]);

  return { violations, loading, error };
}

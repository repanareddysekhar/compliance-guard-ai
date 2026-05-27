import { useState, useEffect } from 'react';
import client from '../api/client';
import { Violation } from '../types';

export function useViolations(scanId?: string) {
  const [violations, setViolations] = useState<Violation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchViolations() {
      setLoading(true);
      try {
        const response = await client.get('/api/violations', {
          params: { scan_id: scanId }
        });
        setViolations(response.data);
        setError(null);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch violations');
      } finally {
        setLoading(false);
      }
    }

    fetchViolations();
  }, [scanId]);

  return { violations, loading, error };
}

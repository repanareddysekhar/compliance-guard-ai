import { useEffect, useState } from 'react';
import client from '../api/client';
import { ScanRun } from '../types';

export function useScanRun(scanId: string | null) {
  const [scanRun, setScanRun] = useState<ScanRun | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!scanId) {
      setScanRun(null);
      setError(null);
      setLoading(false);
      return;
    }

    let cancelled = false;
    let intervalId: number | undefined;

    const fetchScanRun = async () => {
      try {
        setLoading(true);
        const response = await client.get<ScanRun>(`/api/scan/${scanId}`);
        if (cancelled) return;
        setScanRun(response.data);
        setError(null);

        if (response.data.status === 'COMPLETED' || response.data.status === 'FAILED') {
          if (intervalId) {
            window.clearInterval(intervalId);
          }
        }
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : 'Failed to fetch scan status');
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    fetchScanRun();
    intervalId = window.setInterval(fetchScanRun, 1500);

    return () => {
      cancelled = true;
      if (intervalId) {
        window.clearInterval(intervalId);
      }
    };
  }, [scanId]);

  return { scanRun, loading, error };
}

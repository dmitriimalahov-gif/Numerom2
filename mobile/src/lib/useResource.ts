import { useCallback, useEffect, useRef, useState } from 'react';
export function useResource<T>(load: () => Promise<T>) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const sequence = useRef(0);
  const reload = useCallback(async () => {
    const current = ++sequence.current;
    setLoading(true); setError(null);
    try { const value = await load(); if (current === sequence.current) setData(value); }
    catch (e) { if (current === sequence.current) setError(e instanceof Error ? e.message : 'Не удалось загрузить данные'); }
    finally { if (current === sequence.current) setLoading(false); }
  }, [load]);
  useEffect(() => { void reload(); return () => { ++sequence.current; }; }, [reload]);
  return {data, error, loading, reload};
}

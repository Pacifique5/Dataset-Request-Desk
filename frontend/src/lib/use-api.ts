"use client";

import { useCallback, useEffect, useState } from "react";

import { ApiError, apiFetch } from "./api";

interface ApiState<T> {
  data: T | null;
  error: ApiError | null;
  loading: boolean;
  reload: () => void;
}

interface Result<T> {
  key: string | null;
  data: T | null;
  error: ApiError | null;
}

/**
 * Fetch JSON from the API for a client component. Re-fetches when `path` changes or
 * `reload()` is called; keeps showing the previous data while the next request is in
 * flight, and ignores responses for a path that is no longer current.
 */
export function useApi<T>(path: string | null): ApiState<T> {
  const [version, setVersion] = useState(0);
  const [result, setResult] = useState<Result<T>>({ key: null, data: null, error: null });
  const key = path === null ? null : `${path}#${version}`;

  useEffect(() => {
    if (path === null || key === null) return;
    let cancelled = false;
    apiFetch<T>(path)
      .then((data) => !cancelled && setResult({ key, data, error: null }))
      .catch(
        (e: unknown) =>
          !cancelled &&
          setResult((prev) => ({
            key,
            data: prev.data,
            error: e instanceof ApiError ? e : new ApiError(0, "Network error"),
          })),
      );
    return () => {
      cancelled = true;
    };
  }, [path, key]);

  const reload = useCallback(() => setVersion((v) => v + 1), []);
  return {
    data: result.data,
    error: result.error,
    loading: key !== null && result.key !== key,
    reload,
  };
}

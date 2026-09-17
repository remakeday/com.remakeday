"use client";

import { useCallback, useState } from "react";
import { ApiError } from "@/contracts/api";

export interface ApiFailure {
  message: string;
  status: number;
  retry: () => void;
}

/**
 * API 호출 래퍼 — 로딩 상태 + 실패 시 에러 토스트·재시도.
 * 백엔드가 안 떠 있어도 화면이 깨지지 않게 하는 단일 통로.
 */
export function useApiAction() {
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState<ApiFailure | null>(null);

  const run = useCallback(async function runInner<T>(
    fn: () => Promise<T>,
    onOk: (value: T) => void | Promise<void>,
    onFail?: (status: number, code?: string) => boolean, // true 반환 시 토스트 억제 (409 등 자체 처리). code: 서버 응답 code (예: request_in_flight)
  ): Promise<boolean> {
    setBusy(true);
    setFailure(null);
    try {
      const value = await fn();
      await onOk(value);
      setBusy(false);
      return true;
    } catch (e) {
      const status = e instanceof ApiError ? e.status : 0;
      const message =
        e instanceof ApiError ? e.detail : "알 수 없는 오류가 발생했습니다";
      setBusy(false);
      const handled = onFail
        ? onFail(status, e instanceof ApiError ? e.code : undefined)
        : false;
      if (!handled) {
        setFailure({
          message,
          status,
          retry: () => {
            void runInner(fn, onOk, onFail);
          },
        });
      }
      return false;
    }
  }, []);

  const clearFailure = useCallback(() => setFailure(null), []);

  return { busy, failure, run, clearFailure };
}

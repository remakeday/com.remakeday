"use client";

import type { ApiFailure } from "@/lib/useApiAction";

export function ErrorToast({
  failure,
  onClose,
}: {
  failure: ApiFailure | null;
  onClose: () => void;
}) {
  if (!failure) return null;
  return (
    <div className="fade-in fixed bottom-4 left-1/2 z-50 w-[min(92vw,28rem)] -translate-x-1/2">
      <div className="border border-ink/40 bg-paper px-4 py-3 text-sm text-ink shadow-lg">
        <p className="mb-2">{failure.message}</p>
        <div className="flex gap-3">
          <button
            type="button"
            onClick={failure.retry}
            className="border border-ink px-3 py-1 text-xs hover:bg-ink hover:text-paper"
          >
            재시도
          </button>
          <button
            type="button"
            onClick={onClose}
            className="px-3 py-1 text-xs opacity-60 hover:opacity-100"
          >
            닫기
          </button>
        </div>
      </div>
    </div>
  );
}

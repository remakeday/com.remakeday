"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/contracts/api";
import { ENTRY_IMAGE } from "@/lib/imageMap";

const BUTTON = "w-full border border-paper px-6 py-2 text-center text-lg hover:bg-paper hover:text-void disabled:opacity-40";

/**
 * 마이페이지 — 진행 중인 판 이어하기와 회원탈퇴만 둔다 (설계 2026-10-16 §3.2).
 * 탈퇴 확인은 브라우저 confirm() 대신 같은 화면에 펼친다.
 */
export default function MyPage() {
  const router = useRouter();
  const [loaded, setLoaded] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [hasActive, setHasActive] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [withdrawing, setWithdrawing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    void (async () => {
      try {
        await api.getMe();
      } catch (e) {
        if (!alive) return;
        if (e instanceof ApiError && e.status === 401) {
          router.replace("/");
          return;
        }
        setLoadError("잠시 뒤 다시 시도해 주세요.");
        setLoaded(true);
        return;
      }
      const active = await api.getActiveAttempt().catch(() => null);
      if (!alive) return;
      setHasActive(Boolean(active?.attempt));
      setLoaded(true);
    })();
    return () => {
      alive = false;
    };
  }, [router]);

  const withdraw = async () => {
    if (withdrawing) return;
    setWithdrawing(true);
    setError(null);
    try {
      await api.withdraw();
      window.location.assign("/");
    } catch (e) {
      setError(e instanceof ApiError ? e.detail : "탈퇴하지 못했습니다. 잠시 뒤 다시 시도해 주세요.");
      setWithdrawing(false);
    }
  };

  return (
    <main className="relative flex min-h-dvh w-full flex-col items-center justify-center overflow-hidden bg-void px-4 py-10 text-paper">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={ENTRY_IMAGE}
        alt=""
        decoding="async"
        className="pointer-events-none fixed inset-0 h-full w-full scale-[1.35] object-cover object-center opacity-40"
      />
      <section className="relative z-10 flex w-full max-w-md flex-col gap-4 border border-paper/40 bg-void/80 p-5">
        <h1 className="text-2xl">마이페이지</h1>
        {!loaded && <p className="opacity-60">불러오는 중…</p>}
        {loadError && <p role="alert">{loadError}</p>}
        {loaded && !loadError && (
          <>
            {hasActive && (
              <Link href="/play?resume=1" className={BUTTON}>
                이어하기
              </Link>
            )}
            {!confirming ? (
              <button type="button" onClick={() => setConfirming(true)} className={BUTTON}>
                회원탈퇴
              </button>
            ) : (
              <div role="group" aria-label="회원탈퇴 확인" className="border border-paper/60 p-4">
                <p className="text-lg leading-relaxed">모든 플레이 기록이 즉시 삭제되며 되돌릴 수 없습니다</p>
                <div className="mt-4 flex gap-3">
                  <button type="button" onClick={() => void withdraw()} disabled={withdrawing} aria-busy={withdrawing} className={BUTTON}>
                    탈퇴
                  </button>
                  <button type="button" onClick={() => setConfirming(false)} disabled={withdrawing} className={BUTTON}>
                    취소
                  </button>
                </div>
              </div>
            )}
            {error && <p role="alert" className="text-orange">{error}</p>}
          </>
        )}
        <Link href="/" className="text-center text-base opacity-70 underline">
          처음 화면으로
        </Link>
      </section>
    </main>
  );
}

"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { API_BASE } from "@/contracts/api";

/** 개발 계정 로그인 — NEXT_PUBLIC_DEV_LOGIN=on 일 때만 랜딩에 붙는다(2026-09-20 제출 전까지). */
export default function DevLoginForm() {
  const router = useRouter();
  const [id, setId] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/dev/login`, {
        method: "POST",
        credentials: "include",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ id, password }),
      });
      if (res.ok) {
        router.push("/play");
        return;
      }
      const body = await res.json().catch(() => null);
      const detail = body?.detail;
      setError(typeof detail === "string" ? detail : detail?.detail ?? "로그인에 실패했다");
    } catch {
      setError("서버에 연결할 수 없다");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="entry-line mt-6 flex flex-col items-center gap-2" style={{ animationDelay: "5s" }}>
      <input aria-label="개발 계정 아이디" value={id} onChange={e => setId(e.target.value)} maxLength={64}
        autoComplete="username" className="w-36 border border-paper/60 bg-transparent px-2 py-1 text-center text-sm" placeholder="id" />
      <input aria-label="개발 계정 비밀번호" type="password" value={password} onChange={e => setPassword(e.target.value)} maxLength={64}
        autoComplete="current-password" className="w-36 border border-paper/60 bg-transparent px-2 py-1 text-center text-sm" placeholder="password" />
      <button type="submit" disabled={busy} className="w-36 border border-paper/60 px-2 py-1 text-sm hover:bg-paper hover:text-void disabled:opacity-50">
        개발 로그인
      </button>
      {error && <p role="alert" className="text-xs text-paper/80">{error}</p>}
    </form>
  );
}

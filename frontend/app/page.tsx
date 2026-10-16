"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { ENTRY_IMAGE, morningImage } from "@/lib/imageMap";
import { preloadImages } from "@/lib/preloadImages";
import { API_BASE, api } from "@/contracts/api";
import DevLoginForm from "@/components/DevLoginForm";
import { ToggleSwitch } from "@/components/ToggleSwitch";
import { audioEnabled, setAudioEnabled } from "@/lib/audioSettings";

/** 진입 카피 — scenario_a adapter.entry_lines에서 첫 줄("세계가 이상하다.")을 뺀 두 줄. */
const ENTRY_LINES = [
  "오늘이 지나면 세계는 멸망한다.",
  "다섯 번의 하루 안에,\n왜 멸망했는지 알아내야 한다.",
];

/**
 * 랜딩 — /play 진입 화면과 같은 A01(복도) 배경 위에 카피가 앉는다.
 * 제목 텍스트는 로고 워드마크(투명 WebP)로 교체 예정.
 */
export default function Home() {
  const [bgmReady, setBgmReady] = useState(false);
  const [bgmOn, setBgmOn] = useState(true);
  const bgmRef = useRef<HTMLAudioElement>(null);
  const bgmButtonRef = useRef<HTMLButtonElement>(null);
  const loginRef = useRef<HTMLButtonElement>(null);
  const [loggedIn, setLoggedIn] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);

  const revealBgm = () => {
    setBgmOn(audioEnabled("bgm"));
    setBgmReady(true);
  };

  useEffect(() => {
    // 늦은 hydration으로 놓친 애니메이션 시작도 확인한다.
    const animation = loginRef.current?.getAnimations()[0];
    if (animation && Number(animation.currentTime) >= Number(animation.effect?.getTiming().delay)) {
      revealBgm();
    }
  }, []);

  useEffect(() => {
    // 세션 쿠키가 유효하면 로그인 버튼 자리에 로그아웃을 띄운다.
    api.getMe().then(() => setLoggedIn(true), () => {});
  }, []);

  const logout = () => {
    setLoggingOut(true);
    api.logout().catch(() => {}).finally(() => {
      setLoggedIn(false);
      setLoggingOut(false);
    });
  };

  useEffect(() => {
    preloadImages([ENTRY_IMAGE, morningImage(0, 1), "/assets/landing/logo_remakeday.webp"]);
  }, []);

  useEffect(() => {
    const audio = bgmRef.current;
    if (!audio || !bgmReady || !bgmOn) return;
    let active = true;
    audio.volume = 0.25;
    const stopListening = () => {
      document.removeEventListener("pointerdown", onInteraction);
      document.removeEventListener("keydown", onInteraction);
    };
    const onInteraction = (event: Event) => {
      if (bgmButtonRef.current?.contains(event.target as Node)) return;
      stopListening();
      void audio.play().catch(() => {});
    };
    void audio.play().catch(() => {
      if (!active) return;
      document.addEventListener("pointerdown", onInteraction);
      document.addEventListener("keydown", onInteraction);
    });
    return () => {
      active = false;
      stopListening();
      audio.pause();
    };
  }, [bgmReady, bgmOn]);

  const toggleBgm = () => {
    setAudioEnabled("bgm", !bgmOn);
    setBgmOn(!bgmOn);
  };

  return (
    <div className="relative flex min-h-dvh w-full flex-col items-center justify-center overflow-hidden bg-void py-10 text-paper">
      <audio ref={bgmRef} src="/audio/game-bgm.mp3" loop preload="none" />
      {bgmReady && <div className="entry-line fixed top-4 right-4 z-50">
        <ToggleSwitch label="BGM" on={bgmOn} onClick={toggleBgm} buttonRef={bgmButtonRef} />
      </div>}
      {/* A01 상·하 여백을 잘라 모바일 세로 화면을 빈 띠 없이 채운다. */}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={ENTRY_IMAGE}
        alt=""
        decoding="async"
        fetchPriority="high"
        className="pointer-events-none fixed inset-0 h-full w-full scale-[1.35] object-cover object-center opacity-40"
      />
      <div className="relative z-10 flex flex-col items-center gap-5 px-8 text-center">
        {/* 흠집 워드마크 — img_LOGO_remakeday_scratch_v2 (알파 정리·크롭본) */}
        <h1 className="mb-6">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/assets/landing/logo_remakeday.webp"
            alt="REMAKE DAY"
            className="w-[min(86vw,680px)]"
          />
        </h1>
        {ENTRY_LINES.map((line, i) => (
          <p
            key={i}
            className="entry-line whitespace-pre-line text-lg leading-relaxed sm:text-xl"
            style={{ animationDelay: `${1 + i * 1.4}s` }}
          >
            {line}
          </p>
        ))}
        {loggedIn && (
          <Link
            href="/mypage"
            className="entry-line mt-10 w-36 border border-paper py-2 text-center text-lg hover:bg-paper hover:text-void"
            style={{ animationDelay: "3.8s" }}
          >
            마이페이지
          </Link>
        )}
        {/* 같은 버튼을 유지해야 로그인↔로그아웃 전환 때 페이드인이 다시 돌지 않는다. */}
        <button
          ref={loginRef}
          type="button"
          onAnimationStart={revealBgm}
          onClick={loggedIn ? logout : () => window.location.assign(`${API_BASE}/api/v1/auth/google/start`)}
          disabled={loggingOut}
          className={`entry-line ${loggedIn ? "" : "mt-10 "}w-36 border border-paper py-2 text-center text-lg hover:bg-paper hover:text-void disabled:opacity-50`}
          style={{ animationDelay: "4.2s" }}
        >
          {loggedIn ? "로그아웃" : "로그인"}
        </button>
        <Link
          href="/play"
          className="entry-line w-36 border border-paper px-10 py-2 text-center text-lg hover:bg-paper hover:text-void"
          style={{ animationDelay: "4.6s" }}
        >
          시작
        </Link>
        {process.env.NEXT_PUBLIC_DEV_LOGIN === "on" && <DevLoginForm />}
      </div>
    </div>
  );
}

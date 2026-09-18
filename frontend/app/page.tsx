"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { ENTRY_IMAGE } from "@/lib/imageMap";
import { API_BASE } from "@/contracts/api";
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
 * 제목 텍스트는 로고 워드마크(투명 PNG)로 교체 예정.
 */
export default function Home() {
  const [bgmReady, setBgmReady] = useState(false);
  const [bgmOn, setBgmOn] = useState(true);
  const bgmRef = useRef<HTMLAudioElement>(null);
  const bgmButtonRef = useRef<HTMLButtonElement>(null);
  const loginRef = useRef<HTMLAnchorElement>(null);

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
      {/* A01 PNG 상·하 여백을 잘라 모바일 세로 화면을 빈 띠 없이 채운다. */}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={ENTRY_IMAGE}
        alt=""
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
        <a
          ref={loginRef}
          onAnimationStart={revealBgm}
          href={`${API_BASE}/api/v1/auth/google/start`}
          className="entry-line mt-10 w-36 border border-paper px-10 py-2 text-center text-lg hover:bg-paper hover:text-void"
          style={{ animationDelay: "4.2s" }}
        >
          로그인
        </a>
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

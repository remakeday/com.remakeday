import Link from "next/link";
import { ENTRY_IMAGE } from "@/lib/imageMap";
import { API_BASE } from "@/contracts/api";
import DevLoginForm from "@/components/DevLoginForm";

/** 진입 카피 — scenario_a adapter.entry_lines에서 첫 줄("세계가 이상하다.")을 뺀 두 줄. */
const ENTRY_LINES = [
  "오늘이 지나면 세계는 멸망한다.",
  "다섯 번의 하루 안에, 왜 멸망했는지 알아내야 한다.",
];

/**
 * 랜딩 — /play 진입 화면과 같은 A01(복도) 배경 위에 카피가 앉는다.
 * 제목 텍스트는 로고 워드마크(투명 PNG)로 교체 예정.
 */
export default function Home() {
  return (
    <div className="relative flex min-h-dvh w-full flex-col items-center justify-center overflow-hidden bg-void py-10 text-paper">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={ENTRY_IMAGE}
        alt=""
        className="pointer-events-none absolute inset-0 h-full w-full object-cover opacity-40"
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
            className="entry-line text-lg leading-relaxed sm:text-xl"
            style={{ animationDelay: `${1 + i * 1.4}s` }}
          >
            {line}
          </p>
        ))}
        <a
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

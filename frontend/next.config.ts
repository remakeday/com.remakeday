import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // dev 도구 배지("N")가 390px에서 인물 카드(왼쪽 아래)를 덮어 클릭을 막는다 — 에러 오버레이는 그대로 뜬다.
  devIndicators: false,
  async headers() {
    return [
      {
        source: "/assets/:path*",
        headers: [
          { key: "Cache-Control", value: "public, max-age=31536000, immutable" },
        ],
      },
    ];
  },
};

export default nextConfig;

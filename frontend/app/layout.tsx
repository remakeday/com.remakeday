import type { Metadata } from "next";
import { Noto_Serif_KR } from "next/font/google";
import "./globals.css";

const notoSerifKr = Noto_Serif_KR({
  subsets: ["latin"],
  weight: ["400", "600", "700"],
  variable: "--font-serif",
  fallback: ["Noto Serif KR", "serif"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "REMAKE DAY",
  description:
    "세계가 이상하다. 오늘이 지나면, 세계는 멸망한다. 왜인지 알아내면 막을 수 있다.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ko">
      <body className={`${notoSerifKr.variable} antialiased`}>{children}</body>
    </html>
  );
}

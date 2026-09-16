import type { Metadata } from "next";
import { Noto_Serif_KR } from "next/font/google";
import { SiteFooter } from "@/components/SiteFooter";
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
    "세계가 이상하다. 오늘이 지나면, 세계는 멸망한다. 다섯 번의 하루 안에, 왜 멸망했는지 알아내야 한다.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ko">
      <body className={`${notoSerifKr.variable} antialiased`}>
        <div className="flex min-h-dvh flex-col bg-void">
          <main className="flex-1 bg-void">{children}</main>
          <SiteFooter />
        </div>
      </body>
    </html>
  );
}

import Link from "next/link";
import { LEGAL } from "@/lib/legal";

export function SiteFooter() {
  return (
    <footer className="border-t border-paper/10 bg-void px-6 py-10 text-paper">
      <div className="mx-auto flex max-w-3xl flex-col items-center gap-2.5 text-center">
        <p className="text-[11px] tracking-wide text-paper/40">
          © 2026 {LEGAL.operator}. {LEGAL.serviceName}. All rights reserved.
        </p>
        <nav
          className="flex flex-wrap items-center justify-center gap-x-2 text-[12px] text-paper/55"
          aria-label="법적 고지"
        >
          <Link href="/privacy" className="hover:text-paper/80">
            개인정보처리방침
          </Link>
          <span aria-hidden="true" className="text-paper/30">
            ·
          </span>
          <Link href="/terms" className="hover:text-paper/80">
            이용약관
          </Link>
        </nav>
      </div>
    </footer>
  );
}

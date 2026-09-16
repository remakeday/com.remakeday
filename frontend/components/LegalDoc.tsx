import Link from "next/link";
import type { ReactNode } from "react";
import { LEGAL } from "@/lib/legal";

export function LegalDoc({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <div className="min-h-dvh bg-void text-paper">
      <article className="mx-auto max-w-3xl px-6 py-12">
        <p className="mb-2 text-sm tracking-wide text-paper/55">
          <Link href="/play" className="underline-offset-4 hover:text-paper hover:underline">
            {LEGAL.serviceName}
          </Link>
        </p>
        <h1 className="mb-2 text-3xl font-semibold tracking-wide text-paper">{title}</h1>
        <p className="mb-10 text-sm text-paper/55">시행일: {LEGAL.effectiveDate}</p>
        <div className="legal-prose space-y-8 text-base leading-relaxed text-paper/90">
          {children}
        </div>
      </article>
    </div>
  );
}

export function LegalSection({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <section className="space-y-3">
      <h2 className="text-xl font-semibold text-paper">{title}</h2>
      {children}
    </section>
  );
}

import type { ReactNode } from "react";
export function ResultSection({ eyebrow, title, children }: { eyebrow: string; title: string; children: ReactNode }) {
 return <section className="rounded-3xl border border-stone-200 bg-white p-6 shadow-sm"><p className="text-xs font-bold uppercase tracking-[0.16em] text-emerald-700">{eyebrow}</p><h2 className="mt-2 text-xl font-semibold text-stone-900">{title}</h2><div className="mt-5 text-sm leading-6 text-stone-600">{children}</div></section>;
}


import { useState } from "react";
export function LessonRequestForm({ onSubmit, isLoading }: { onSubmit: (description: string) => Promise<void>; isLoading: boolean }) {
  const [description, setDescription] = useState(""); const valid = description.trim().length >= 10;
  return <form className="rounded-3xl border border-emerald-900/10 bg-white p-6 shadow-sm sm:p-8" onSubmit={(e) => { e.preventDefault(); if (valid) void onSubmit(description.trim()); }}>
    <label htmlFor="lesson-description" className="text-base font-semibold text-stone-900">Cuéntale a Clara sobre tu clase</label>
    <p className="mt-2 text-sm leading-6 text-stone-500">Incluye curso, asignatura, tema, duración y cualquier necesidad de tus estudiantes.</p>
    <textarea id="lesson-description" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Ej.: Necesito una clase de 90 minutos para 6° básico sobre el ciclo del agua, con una actividad práctica y evaluación de salida." className="mt-5 min-h-36 w-full resize-y rounded-2xl border border-stone-200 bg-stone-50 p-4 text-stone-800 outline-none transition placeholder:text-stone-400 focus:border-emerald-700 focus:ring-4 focus:ring-emerald-700/10" />
    <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><span className="text-xs text-stone-400">{description.length}/4000 caracteres</span><button type="submit" disabled={!valid || isLoading} className="rounded-full bg-emerald-800 px-5 py-3 text-sm font-semibold text-white transition hover:bg-emerald-900 disabled:cursor-not-allowed disabled:opacity-40">{isLoading ? "Preparando tu pack…" : "Crear pack de enseñanza"}</button></div>
  </form>;
}


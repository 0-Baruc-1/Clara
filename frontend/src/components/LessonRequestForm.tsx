import { useState, type FormEvent } from "react";
import type { LessonRequest } from "../types/teachingPack";

export function LessonRequestForm({ onSubmit }: { onSubmit: (request: LessonRequest) => Promise<void> }) {
  const [subject, setSubject] = useState("Ciencias Naturales");
  const [grade, setGrade] = useState("6° básico");
  const [topic, setTopic] = useState("Cambios de estado del agua");
  const [duration, setDuration] = useState(90);
  const [notes, setNotes] = useState("Actividad práctica y una verificación formativa al cierre.");
  const submit = (event: FormEvent) => {
    event.preventDefault();
    const description = `Clase de ${subject} para ${grade}, ${duration} minutos. Tema: ${topic}. ${notes}`;
    void onSubmit({ description, subject, grade_level: grade, topic, duration_minutes: duration, notes });
  };
  return <form className="rounded-[2rem] border border-stone-200 bg-white p-6 shadow-[0_18px_55px_-28px_rgba(28,60,51,.35)] sm:p-9" onSubmit={submit}>
    <div className="grid gap-5 sm:grid-cols-2"><label className="field"><span>Asignatura</span><input value={subject} onChange={(e) => setSubject(e.target.value)} required /></label><label className="field"><span>Curso</span><input value={grade} onChange={(e) => setGrade(e.target.value)} required /></label><label className="field sm:col-span-2"><span>¿Qué quieres enseñar?</span><input value={topic} onChange={(e) => setTopic(e.target.value)} required /></label><label className="field"><span>Duración</span><select value={duration} onChange={(e) => setDuration(Number(e.target.value))}><option value={45}>45 minutos</option><option value={60}>60 minutos</option><option value={90}>90 minutos</option></select></label><div className="rounded-2xl bg-amber-50 px-4 py-3 text-sm leading-5 text-amber-900">Clara buscará OA reales en la base curricular disponible y mostrará cualquier límite con transparencia.</div><label className="field sm:col-span-2"><span>Notas para Clara <em>(opcional)</em></span><textarea value={notes} onChange={(e) => setNotes(e.target.value)} rows={3} placeholder="Necesidades del curso, recursos disponibles, énfasis pedagógico…" /></label></div>
    <div className="mt-7 flex flex-col gap-3 border-t border-stone-100 pt-6 sm:flex-row sm:items-center sm:justify-between"><p className="text-sm text-stone-500">Plan, actividades y criterios curriculares en un solo flujo.</p><button className="rounded-full bg-[#195b4e] px-6 py-3.5 text-sm font-semibold text-white transition hover:bg-[#10473c]">Crear mi clase <span aria-hidden>→</span></button></div>
  </form>;
}

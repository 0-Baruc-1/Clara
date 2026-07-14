import type { TeachingPack } from "../types/teachingPack";
import { ResultSection } from "./ResultSection";
const List = ({ items }: { items: string[] }) => <ul className="space-y-2">{items.map((item) => <li key={item} className="flex gap-2"><span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-600" />{item}</li>)}</ul>;
export function TeachingPackResults({ pack }: { pack: TeachingPack }) {
 return <div className="mt-10 space-y-5"><div><p className="text-sm font-semibold text-emerald-700">Tu pack está listo</p><h1 className="mt-1 text-3xl font-semibold tracking-tight text-stone-900">Una clase coherente, lista para adaptar.</h1></div><div className="grid gap-5 lg:grid-cols-3">
 <ResultSection eyebrow="01 · Plan" title={pack.lesson_plan.title}><p className="mb-4 text-stone-500">{pack.lesson_plan.duration_minutes} minutos</p><p className="mb-2 font-semibold text-stone-800">Objetivos</p><List items={pack.lesson_plan.learning_objectives} /><p className="mb-2 mt-5 font-semibold text-stone-800">Secuencia</p><List items={pack.lesson_plan.sequence} /></ResultSection>
 <ResultSection eyebrow="02 · Actividad" title={pack.activities.title}><p className="mb-2 font-semibold text-stone-800">Materiales</p><List items={pack.activities.materials} /><p className="mb-2 mt-5 font-semibold text-stone-800">Pasos</p><List items={pack.activities.instructions} /></ResultSection>
 <ResultSection eyebrow="03 · Evaluación" title={pack.assessment.title}><List items={pack.assessment.instructions} /><div className="mt-5 overflow-hidden rounded-xl border border-stone-200"><table className="w-full text-left text-xs"><thead className="bg-stone-50 text-stone-500"><tr><th className="p-2">Criterio</th><th className="p-2">Logrado</th></tr></thead><tbody>{pack.assessment.rubric.map((row) => <tr key={row.criterion} className="border-t border-stone-200"><td className="p-2 font-medium text-stone-800">{row.criterion}</td><td className="p-2">{row.achieved}</td></tr>)}</tbody></table></div></ResultSection>
 </div>{pack.review_notes.length > 0 && <p className="rounded-2xl bg-emerald-50 px-5 py-4 text-sm text-emerald-900">Revisión de Clara: {pack.review_notes.join(" ")}</p>}</div>;
}


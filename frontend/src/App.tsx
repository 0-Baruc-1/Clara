import { useState } from "react";
import { LessonRequestForm } from "./components/LessonRequestForm";
import { TeachingPackResults } from "./components/TeachingPackResults";
import { generateTeachingPack } from "./lib/api";
import type { TeachingPack } from "./types/teachingPack";

export default function App() {
 const [pack, setPack] = useState<TeachingPack | null>(null); const [isLoading, setIsLoading] = useState(false); const [error, setError] = useState<string | null>(null);
 async function handleSubmit(description: string) { setIsLoading(true); setError(null); try { setPack(await generateTeachingPack({ description })); } catch (caught) { setError(caught instanceof Error ? caught.message : "Ocurrió un error inesperado."); } finally { setIsLoading(false); } }
 return <main className="min-h-screen bg-[#f8f7f2]"><div className="mx-auto max-w-6xl px-5 py-10 sm:px-8 sm:py-16"><header className="mb-12 flex items-center justify-between"><div className="flex items-center gap-3"><div className="grid h-10 w-10 place-items-center rounded-2xl bg-emerald-800 text-lg font-bold text-white">C</div><span className="text-lg font-semibold tracking-tight text-stone-900">Clara</span></div><span className="rounded-full border border-emerald-900/10 bg-white px-3 py-1 text-xs font-medium text-emerald-800">Copiloto pedagógico</span></header><div className="max-w-3xl"><p className="text-sm font-semibold text-emerald-700">Planifica con intención</p><h1 className="mt-3 text-4xl font-semibold tracking-tight text-stone-900 sm:text-5xl">De una idea de clase a un pack listo para enseñar.</h1><p className="mt-5 max-w-2xl text-lg leading-8 text-stone-600">Clara ayuda a docentes de Chile a crear planificaciones, actividades y evaluaciones conectadas entre sí.</p></div><div className="mt-10 max-w-3xl"><LessonRequestForm onSubmit={handleSubmit} isLoading={isLoading} />{error && <p role="alert" className="mt-4 text-sm text-red-700">{error}</p>}</div>{pack && <TeachingPackResults pack={pack} />}</div></main>;
}


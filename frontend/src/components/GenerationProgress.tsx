import { ClaraMark, type ClaraMarkState } from "./ClaraMark";
import type { ActivityGuide, Assessment, LessonPlan } from "../types/teachingPack";

type Status = "pending" | "working" | "correcting" | "done";
type Props = { planner: Status; designer: Status; assessment: Status; reviewer: Status; handoff: string | null; toolSummary: string | null; plan: LessonPlan | null; guide: ActivityGuide | null; instrument: Assessment | null };

const stateCopy: Record<Status, string> = { pending: "En espera", working: "Trabajando", correcting: "Ajustando", done: "Listo" };
const stateTone: Record<Status, string> = { pending: "text-stone-400", working: "text-[#195b4e]", correcting: "text-[#aa5d31]", done: "text-emerald-700" };

function AgentCard({ name, detail, status, preview }: { name: string; detail: string; status: Status; preview?: string }) {
  return <article className={`agent-card agent-card--${status} rounded-2xl border p-5 transition-colors duration-500 ${status === "working" ? "border-[#a9cbbb] bg-[#edf6f1]" : status === "correcting" ? "border-[#e5b18b] bg-[#fff6ee]" : status === "done" ? "border-emerald-200 bg-white" : "border-stone-200 bg-white/60"}`}>
    <div className="flex items-start justify-between gap-4"><div><h3 className="font-serif text-xl text-stone-900">{name}</h3><p className="mt-1 text-sm text-stone-500">{detail}</p></div><span className={`text-xs font-bold uppercase tracking-[.12em] ${stateTone[status]}`}>{stateCopy[status]}</span></div>
    {status === "working" && <div className="agent-activity mt-5" aria-label={`${name} está trabajando`}><span /></div>}
    {status === "correcting" && <div className="agent-return mt-5" aria-label={`${name} está aplicando una corrección`}><span /></div>}
    {status === "done" && <div className="agent-reveal mt-5 rounded-xl bg-emerald-50 px-4 py-3 text-sm text-emerald-900"><span className="mr-2 font-bold">✓</span>{preview}</div>}
  </article>;
}

export function GenerationProgress({ planner, designer, assessment, reviewer, handoff, toolSummary, plan, guide, instrument }: Props) {
  const markState: ClaraMarkState = handoff ? "correcting" : reviewer === "done" ? "done" : [planner, designer, assessment, reviewer].includes("working") ? "working" : "resting";
  return <section className="mx-auto mt-10 max-w-3xl">
    <div className="flex flex-col items-center text-center"><ClaraMark state={markState} size="lg" /><p className="mt-4 text-sm font-semibold tracking-[.16em] text-[#195b4e]">CLARA ESTÁ PREPARANDO TU CLASE</p><h2 className="mt-3 font-serif text-4xl text-stone-900">Un equipo construye y revisa cada decisión.</h2><p className="mt-3 max-w-xl text-stone-600">Cada avance aparece cuando está listo. Mientras tanto, Clara te muestra quién está trabajando.</p></div>
    <div className="mt-10 space-y-3">
      <AgentCard name="Planificador" detail="Conecta objetivos, estructura y tiempo de clase." status={planner} preview={plan ? `Plan listo: ${plan.title}` : undefined} />
      <AgentCard name="Diseñador" detail="Convierte el plan en experiencias concretas de aula." status={designer} preview={guide ? `${guide.activities.length} actividades diseñadas para tu clase.` : undefined} />
      <AgentCard name="Evaluador" detail="Construye un instrumento y su rúbrica." status={assessment} preview={instrument ? `${instrument.items.length} ítems y rúbrica listos.` : undefined} />
      <AgentCard name="Revisor" detail="Comprueba que lo planificado, enseñado y evaluado sea coherente." status={reviewer} preview={reviewer === "done" ? "Revisión de coherencia completada." : undefined} />
    </div>
    {toolSummary && <p className="mt-4 rounded-xl bg-white px-4 py-3 text-center text-sm text-[#195b4e] ring-1 ring-[#d7e6dc]">{toolSummary}</p>}
    {handoff && <aside className="correction-handoff mt-6 rounded-2xl border border-[#e5b18b] bg-[#fff8f2] p-6 text-stone-700" aria-live="polite"><div className="flex items-center gap-4"><ClaraMark state="correcting" size="sm" /><div><p className="font-serif text-2xl text-[#82421f]">Clara encontró algo que ajustar</p><p className="mt-1 text-sm">{handoff}</p></div></div><div className="mt-5 flex items-center gap-3 text-sm font-semibold text-[#9a522b]"><span className="h-px flex-1 bg-[#e5b18b]" />El material vuelve al equipo para corregirse<span className="h-px flex-1 bg-[#e5b18b]" /></div></aside>}
  </section>;
}

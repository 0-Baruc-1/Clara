import type { ActivityGuide, Assessment, LessonPlan, MaterialPack, ReviewFinding, ReviewReport } from "../types/teachingPack";
import { ResultSection } from "./ResultSection";

const List = ({ items }: { items: string[] }) => (
  <ul className="space-y-2">{items.map((item) => <li key={item}>• {item}</li>)}</ul>
);
const printTarget = (target: "full" | "student" | "materials") => { document.body.dataset.printTarget = target; window.print(); window.setTimeout(() => delete document.body.dataset.printTarget, 0); };

function ReviewNotes({ findings }: { findings: ReviewFinding[] }) {
  if (!findings.length) return null;
  const style = { bloqueante: "bg-rose-50 text-rose-900 ring-rose-200", importante: "bg-amber-50 text-amber-900 ring-amber-200", menor: "bg-sky-50 text-sky-900 ring-sky-200" };
  return <aside className="no-print mt-6 space-y-3" aria-label="Observaciones de revisión de Clara">
    <p className="text-sm font-semibold text-stone-700">Clara deja visibles estas observaciones sobre su propio material</p>
    {findings.map((finding) => <article key={finding.id} className={`rounded-xl p-4 ring-1 ${style[finding.severity]}`}>
      <div className="flex flex-wrap items-center gap-2 text-xs font-semibold uppercase tracking-wide">
        <span>{finding.severity}</span><span className="normal-case tracking-normal">{finding.artifact_id}</span>
      </div>
      <p className="mt-2 font-medium">{finding.description}</p>
      <p className="mt-2 text-sm"><b>Sugerencia de Clara:</b> {finding.suggested_correction}</p>
    </article>)}
  </aside>;
}

export function TeachingPackResults({ plan, guide, assessment, review, materials, onGenerateMaterials, materialsBusy }: { plan: LessonPlan; guide: ActivityGuide; assessment: Assessment; review: ReviewReport; materials: MaterialPack | null; onGenerateMaterials: () => void; materialsBusy: boolean }) {
  const grouped = guide.activities.reduce<Record<string, typeof guide.activities>>((all, activity) => { (all[activity.stage_name] ??= []).push(activity); return all; }, {});
  const findingsFor = (agent: ReviewFinding["responsible_agent"]) => review.findings.filter((finding) => finding.responsible_agent === agent);
  const passed = review.status === "clean" && !review.findings.length;

  return <div className="teaching-pack mt-12 space-y-10">
    <div className="no-print flex flex-col gap-5 border-b border-stone-200 pb-7 sm:flex-row sm:items-start sm:justify-between">
      <div><p className="text-sm font-semibold uppercase tracking-[0.16em] text-[#3b7969]">Pack de enseñanza</p><h1 className="mt-2 font-serif text-4xl text-stone-900">{plan.title}</h1>
        <div className={`mt-4 max-w-2xl rounded-xl px-4 py-3 text-sm ${passed ? "bg-emerald-50 text-emerald-900" : "bg-amber-50 text-amber-950"}`}>
          <b>{passed ? "Revisión de coherencia superada" : "Clara revisó el pack con transparencia"}</b>
          <p className="mt-1">{passed ? "Plan, actividades y evaluación fueron revisados en conjunto antes de llegar a ti." : "Estas observaciones son sobre el material generado por Clara, no sobre tu solicitud. Puedes revisarlas con calma antes de usar el pack."}</p>
        </div>
      </div>
      <div className="flex flex-wrap gap-2"><button className="rounded-lg border border-stone-300 px-4 py-2 text-sm font-semibold text-stone-700 hover:bg-stone-50" onClick={() => printTarget("full")}>Imprimir pack</button><button className="rounded-lg border border-stone-300 px-4 py-2 text-sm font-semibold text-stone-700 hover:bg-stone-50" onClick={() => printTarget("student")}>Evaluación estudiante</button>{materials && <button className="rounded-lg border border-stone-300 px-4 py-2 text-sm font-semibold text-stone-700 hover:bg-stone-50" onClick={() => printTarget("materials")}>Materiales</button>}</div>
    </div>

    <ResultSection eyebrow="Plan de clase" title="Propósito y ruta de aprendizaje">
      <p>{plan.subject} · {plan.grade_level} · {plan.duration_minutes} min</p>
      <div className="mt-5 rounded-xl bg-emerald-50 p-4"><b>{plan.curriculum_alignment.status}</b>{plan.curriculum_alignment.objectives.map((oa) => <p key={oa.code}><b>{oa.code}</b> · {oa.description}</p>)}<List items={plan.curriculum_alignment.notes} /></div>
      <List items={plan.learning_objectives} />
      <div className="mt-5">{plan.stages.map((stage) => <p key={stage.name}><b>{stage.name} · {stage.duration_minutes} min:</b> {stage.purpose}</p>)}</div>
      <ReviewNotes findings={findingsFor("planner")} />
    </ResultSection>

    <div className="print-break"><ResultSection eyebrow="Actividades" title={guide.title}>
      {plan.stages.map((stage) => <section key={stage.name} className="mt-6"><h3>{stage.name}</h3>{(grouped[stage.name] ?? []).map((activity) => <article key={activity.id} className="mt-3 rounded-xl bg-[#fbfaf6] p-4"><b>{activity.title} · {activity.duration_minutes} min · {activity.grouping}</b><List items={activity.teacher_instructions} /><p><b>Producto:</b> {activity.expected_student_output}</p><p><b>Apoyo:</b> {activity.differentiation.support}</p><p><b>Extensión:</b> {activity.differentiation.extension}</p></article>)}</section>)}
      <ReviewNotes findings={findingsFor("designer")} />
    </ResultSection></div>

    <div className="print-break"><ResultSection eyebrow="Evaluación" title={assessment.title}>
      <p>{assessment.suggested_application_minutes} min · {assessment.total_points} puntos</p>
      <table className="mt-4 w-full text-left text-sm"><tbody>{assessment.specification_table.map((row) => <tr key={row.learning_objective}><td>{row.learning_objective}</td><td>{row.item_ids.join(", ")}</td><td>{row.total_points} pts</td><td>{row.cognitive_levels.join(", ")}</td></tr>)}</tbody></table>
      {assessment.items.map((item) => <article key={item.id} className="mt-5 rounded-xl bg-[#fbfaf6] p-4"><p><b>{item.id}. {item.question}</b> ({item.points} pts)</p>{item.options.map((option) => <p key={option.label} className={option.label === item.correct_option_label ? "font-bold text-[#195b4e]" : ""}>{option.label}. {option.text}{option.label === item.correct_option_label && " ✓"}</p>)}{item.correct_option_label && <p><b>Alternativa correcta:</b> {item.correct_option_label}</p>}<p><b>Criterio / respuesta esperada:</b> {item.expected_answer}</p></article>)}
      {assessment.rubric.map((criterion) => <article key={criterion.criterion} className="mt-4 rounded-xl border p-4"><b>{criterion.criterion}</b><p>Logrado: {criterion.levels.logrado}</p><p>En proceso: {criterion.levels.en_proceso}</p><p>Requiere apoyo: {criterion.levels.requiere_apoyo}</p></article>)}
      <ReviewNotes findings={findingsFor("assessment")} />
    </ResultSection></div>
    <div className="student-assessment print-student print-break"><ResultSection eyebrow="Evaluación para estudiantes" title={assessment.title}>
      <List items={assessment.instructions} />{assessment.items.map((item) => <article key={item.id} className="mt-5"><p><b>{item.id}. {item.question}</b> ({item.points} pts)</p>{item.options.map((option) => <p key={option.label}>○ {option.label}. {option.text}</p>)}{item.type !== "selección múltiple" && <div className="mt-3 h-20 border-b border-stone-400" />}</article>)}
    </ResultSection></div>
    <div className="print-break"><ResultSection eyebrow="Materiales imprimibles" title={materials?.title ?? "Hojas para el aula"}>
      {!materials && <div className="no-print rounded-xl bg-[#fff8f2] p-5"><p>Genera las hojas solicitadas por las actividades. Clara las revisará antes de entregártelas.</p><button disabled={materialsBusy} onClick={onGenerateMaterials} className="mt-4 rounded-lg bg-[#195b4e] px-4 py-2 text-sm font-semibold text-white disabled:opacity-60">{materialsBusy ? "Materiales y Revisor trabajando…" : "Generar materiales imprimibles"}</button></div>}
      {materials?.materials.map((material) => <article key={material.id} className="print-break mt-5 rounded-xl border border-stone-200 p-6"><p className="text-xs font-bold uppercase tracking-wide text-[#3b7969]">{material.source_material_label}</p><h3 className="mt-2">{material.title}</h3><List items={material.student_instructions} />{material.content.map((block, index) => <div key={index} className="mt-4">{block.title && <b>{block.title}</b>}{block.content && <p>{block.content}</p>}{block.type === "tabla" && <table className="mt-2 w-full border-collapse text-sm"><tbody><tr>{block.columns.map((column) => <th key={column} className="border p-2 text-left">{column}</th>)}</tr>{block.rows.map((row, rowIndex) => <tr key={rowIndex}>{row.map((cell, cellIndex) => <td key={cellIndex} className="h-8 border p-2">{cell}</td>)}</tr>)}</tbody></table>}{block.type === "tarjetas" && <div className="mt-2 grid grid-cols-2 gap-2">{block.cards.map((card, cardIndex) => <div key={cardIndex} className="border p-3">{card.front}<hr className="my-2" />{card.back}</div>)}</div>}</div>)}</article>)}
      {materials && <ReviewNotes findings={findingsFor("materials")} />}
    </ResultSection></div>
  </div>;
}

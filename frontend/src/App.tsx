import { useState } from "react";
import { ClaraMark, type ClaraMarkState } from "./components/ClaraMark";
import { GenerationProgress } from "./components/GenerationProgress";
import { LessonRequestForm } from "./components/LessonRequestForm";
import { TeachingPackResults } from "./components/TeachingPackResults";
import { AuditWorkspace } from "./components/AuditWorkspace";
import { CoverageWorkspace } from "./components/CoverageWorkspace";
import { generateMaterialsStream, generateTeachingPackStream, isMockMode, reviewEditedPackStream, type MockSpeed } from "./lib/api";
import type { ActivityGuide, Assessment, LessonPlan, LessonRequest, MaterialPack, ReviewReport } from "./types/teachingPack";

type Status = "pending" | "working" | "correcting" | "done";

export default function App() {
  const [screen, setScreen] = useState<"request" | "generating" | "results" | "audit" | "coverage">("request");
  const [plan, setPlan] = useState<LessonPlan | null>(null);
  const [guide, setGuide] = useState<ActivityGuide | null>(null);
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [review, setReview] = useState<ReviewReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [planner, setPlanner] = useState<Status>("pending");
  const [designer, setDesigner] = useState<Status>("pending");
  const [evaluator, setEvaluator] = useState<Status>("pending");
  const [reviewer, setReviewer] = useState<Status>("pending");
  const [handoff, setHandoff] = useState<string | null>(null);
  const [toolSummary, setToolSummary] = useState<string | null>(null);
  const [mockSpeed, setMockSpeed] = useState<MockSpeed>("normal");
  const [materials, setMaterials] = useState<MaterialPack | null>(null);
  const [materialsBusy, setMaterialsBusy] = useState(false);
  const [hasEdits, setHasEdits] = useState(false);
  const [editReviewBusy, setEditReviewBusy] = useState(false);
  const [editReviewError, setEditReviewError] = useState<string | null>(null);
  const [editReviewStatus, setEditReviewStatus] = useState<string | null>(null);
  const [showGenerator, setShowGenerator] = useState(false);

  async function start(request: LessonRequest) {
    setScreen("generating"); setPlan(null); setGuide(null); setAssessment(null); setReview(null); setMaterials(null); setHasEdits(false); setEditReviewError(null); setEditReviewStatus(null); setError(null);
    setPlanner("working"); setDesigner("pending"); setEvaluator("pending"); setReviewer("pending"); setHandoff(null); setToolSummary(null);
    try {
      await generateTeachingPackStream(request, (event) => {
        if (event.type === "agent_tool_completed") setToolSummary(event.summary);
        if (event.type === "planner_completed") { setPlan(event.plan); setPlanner("done"); }
        if (event.type === "designer_started") setDesigner("working");
        if (event.type === "designer_completed") { setGuide(event.activities); setDesigner("done"); }
        if (event.type === "assessment_started") setEvaluator("working");
        if (event.type === "assessment_completed") { setAssessment(event.assessment); setEvaluator("done"); }
        if (event.type === "reviewer_started") setReviewer("working");
        if (event.type === "reviewer_correcting") {
          setHandoff(`El Revisor detectó una inconsistencia y pidió al ${event.target_agent === "assessment" ? "Evaluador" : "Diseñador"} corregirla antes de entregar tu pack.`);
          if (event.target_agent === "assessment") setEvaluator("correcting"); else setDesigner("correcting");
        }
        if (event.type === "reviewer_completed") { setReview(event.review); setGuide(event.activities); setAssessment(event.assessment); setReviewer("done"); setDesigner("done"); setEvaluator("done"); setScreen("results"); }
        if (event.type === "failure") { setError(event.message); setScreen("request"); }
      }, { mock: isMockMode, mockSpeed });
    } catch (caught) { setError(caught instanceof Error ? caught.message : "No fue posible preparar tu material."); setScreen("request"); }
  }

  async function createMaterials(pack: { lesson_plan: LessonPlan; activities: ActivityGuide; assessment: Assessment; materials: MaterialPack | null }) {
    setMaterialsBusy(true); setError(null);
    try { await generateMaterialsStream(pack, (event) => { if (event.type === "materials_completed" || event.type === "materials_reviewer_completed") setMaterials(event.materials); if (event.type === "materials_failure") setError(event.message); }, { mock: isMockMode, mockSpeed }); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "No fue posible preparar los materiales."); } finally { setMaterialsBusy(false); }
  }

  async function reviewEdits(pack: { lesson_plan: LessonPlan; activities: ActivityGuide; assessment: Assessment; materials: MaterialPack | null }) {
    setEditReviewBusy(true); setEditReviewError(null); setEditReviewStatus("Clara está revisando la versión editada.");
    try { await reviewEditedPackStream(pack, (event) => { if (event.type === "edited_review_started") setEditReviewStatus(event.message); if (event.type === "agent_tool_completed") setEditReviewStatus(event.summary); if (event.type === "edited_review_completed") { setReview(event.review); setHasEdits(false); setEditReviewStatus("Revisión de cambios completada."); } if (event.type === "edited_review_failure") { setEditReviewError(event.message); setEditReviewStatus(null); } }, { mock: isMockMode, mockSpeed }); }
    catch (caught) { setEditReviewError(caught instanceof Error ? caught.message : "No fue posible revisar los cambios."); } finally { setEditReviewBusy(false); }
  }

  const changedPlan = (next: LessonPlan) => { setPlan(next); setHasEdits(true); };
  const changedGuide = (next: ActivityGuide) => { setGuide(next); setHasEdits(true); };
  const changedAssessment = (next: Assessment) => { setAssessment(next); setHasEdits(true); };
  const changedMaterials = (next: MaterialPack) => { setMaterials(next); setHasEdits(true); };

  const headerMarkState: ClaraMarkState = screen === "generating" ? handoff ? "correcting" : "working" : "resting";
  const openGenerator = () => {
    setShowGenerator(true);
    window.setTimeout(() => document.getElementById("crear-clase")?.scrollIntoView({ behavior: "smooth", block: "start" }), 0);
  };
  return <main className="min-h-screen bg-[#f7f4ed]"><div className="mx-auto max-w-6xl px-5 py-8 sm:px-8 sm:py-12">
    <header className="no-print flex items-center gap-3"><ClaraMark state={headerMarkState} size="sm" /><div><p className="font-serif text-xl font-semibold text-stone-900">Clara</p><p className="text-xs text-stone-500">Compañera de planificación docente</p></div>{isMockMode && <details className="ml-auto text-xs text-stone-500"><summary className="cursor-pointer rounded-full border border-stone-200 bg-white px-3 py-1.5 font-semibold marker:content-none">Vista previa</summary><label className="mt-2 flex items-center gap-2 rounded-lg bg-white p-2 shadow-sm">Velocidad <select value={mockSpeed} onChange={(event) => setMockSpeed(event.target.value as MockSpeed)} className="rounded border border-stone-300 bg-white px-1.5 py-1"><option value="slow">Lenta</option><option value="normal">Normal</option><option value="fast">Rápida</option></select></label></details>}</header>
    {screen === "request" && <div className="mx-auto mt-14 max-w-5xl"><div className="max-w-3xl"><p className="text-sm font-bold tracking-[.12em] text-[#c36c3e]">PLANIFICA Y VERIFICA CON CALMA</p><h1 className="mt-4 font-serif text-5xl text-stone-900">Una buena clase empieza con una intención clara.</h1><p className="mt-5 max-w-2xl text-lg leading-8 text-stone-600">Crea una clase o trae material que ya existe: Clara verifica sus afirmaciones curriculares y su coherencia antes de que lleguen a tu curso.</p></div><div className="mt-10 grid gap-4 md:grid-cols-3">
      <button onClick={openGenerator} className="group min-h-64 rounded-[1.7rem] border border-stone-200 bg-white p-6 text-left shadow-[0_12px_35px_-28px_rgba(28,60,51,.45)] transition hover:-translate-y-0.5 hover:border-[#7eaa9e] hover:shadow-md"><p className="text-xs font-bold tracking-[.14em] text-[#3b7969]">CREAR</p><h2 className="mt-4 font-serif text-3xl text-stone-900">Crear un pack de clase</h2><p className="mt-3 leading-6 text-stone-600">Plan, actividades y evaluación conectados en un solo flujo.</p><span className="mt-7 inline-block font-semibold text-[#195b4e]">Empezar una clase →</span></button>
      <button onClick={() => setScreen("audit")} className="group min-h-64 rounded-[1.7rem] border-2 border-[#3b7969] bg-[#edf5f0] p-6 text-left shadow-[0_12px_35px_-28px_rgba(28,60,51,.45)] transition hover:-translate-y-0.5 hover:bg-[#e4f0e9] hover:shadow-md"><p className="text-xs font-bold tracking-[.14em] text-[#195b4e]">VERIFICAR</p><h2 className="mt-4 font-serif text-3xl text-stone-900">Auditar material existente</h2><p className="mt-3 leading-6 text-stone-700">Trae una planificación o evaluación de cualquier origen. Clara contrasta OA, evidencia y coherencia.</p><span className="mt-7 inline-block font-semibold text-[#195b4e]">Auditar un material →</span></button>
      <button onClick={() => setScreen("coverage")} className="group min-h-64 rounded-[1.7rem] border border-stone-200 bg-white p-6 text-left shadow-[0_12px_35px_-28px_rgba(28,60,51,.45)] transition hover:-translate-y-0.5 hover:border-[#7eaa9e] hover:shadow-md"><p className="text-xs font-bold tracking-[.14em] text-[#c36c3e]">SEGUIR</p><h2 className="mt-4 font-serif text-3xl text-stone-900">Ver cobertura curricular</h2><p className="mt-3 leading-6 text-stone-600">Mira los OA que Clara ha podido verificar a lo largo de tus packs.</p><span className="mt-7 inline-block font-semibold text-[#195b4e]">Explorar cobertura →</span></button>
    </div>{showGenerator && <div id="crear-clase" className="mt-12 scroll-mt-8"><div className="mb-5 flex items-end justify-between gap-4"><div><p className="text-sm font-bold tracking-[.12em] text-[#3b7969]">CREAR UN PACK</p><h2 className="mt-2 font-serif text-3xl text-stone-900">Cuéntale a Clara sobre tu clase.</h2></div><button className="text-sm font-semibold text-stone-500 underline" onClick={() => setShowGenerator(false)}>Cerrar</button></div><LessonRequestForm onSubmit={start} />{error && <p className="mt-4 rounded-xl bg-red-50 p-4 text-sm text-red-800">{error}</p>}</div>}</div>}
    {screen === "generating" && <GenerationProgress planner={planner} designer={designer} assessment={evaluator} reviewer={reviewer} handoff={handoff} toolSummary={toolSummary} plan={plan} guide={guide} instrument={assessment} />}
    {screen === "audit" && <><button className="no-print mt-8 text-sm font-semibold text-[#195b4e] underline" onClick={() => setScreen("request")}>← Volver</button><AuditWorkspace /></>}
    {screen === "coverage" && <CoverageWorkspace mock={isMockMode} onBack={() => setScreen(plan ? "results" : "request")} />}
    {screen === "results" && plan && guide && assessment && review && <TeachingPackResults plan={plan} guide={guide} assessment={assessment} review={review} materials={materials} onPlanChange={changedPlan} onGuideChange={changedGuide} onAssessmentChange={changedAssessment} onMaterialsChange={changedMaterials} onGenerateMaterials={createMaterials} materialsBusy={materialsBusy} onReviewEdits={reviewEdits} editReviewBusy={editReviewBusy} editReviewError={editReviewError} editReviewStatus={editReviewStatus} hasEdits={hasEdits} onReplay={isMockMode ? () => { setShowGenerator(true); setScreen("request"); } : undefined} />}
  </div></main>;
}

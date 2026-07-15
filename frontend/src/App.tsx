import { useState } from "react";
import { ClaraMark, type ClaraMarkState } from "./components/ClaraMark";
import { GenerationProgress } from "./components/GenerationProgress";
import { LessonRequestForm } from "./components/LessonRequestForm";
import { TeachingPackResults } from "./components/TeachingPackResults";
import { generateMaterialsStream, generateTeachingPackStream, isMockMode, type MockSpeed } from "./lib/api";
import type { ActivityGuide, Assessment, LessonPlan, LessonRequest, MaterialPack, ReviewReport } from "./types/teachingPack";

type Status = "pending" | "working" | "correcting" | "done";

export default function App() {
  const [screen, setScreen] = useState<"request" | "generating" | "results">("request");
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
  const [mockSpeed, setMockSpeed] = useState<MockSpeed>("normal");
  const [materials, setMaterials] = useState<MaterialPack | null>(null);
  const [materialsBusy, setMaterialsBusy] = useState(false);

  async function start(request: LessonRequest) {
    setScreen("generating"); setPlan(null); setGuide(null); setAssessment(null); setReview(null); setError(null);
    setPlanner("working"); setDesigner("pending"); setEvaluator("pending"); setReviewer("pending"); setHandoff(null);
    try {
      await generateTeachingPackStream(request, (event) => {
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

  async function createMaterials() {
    if (!plan || !guide || !assessment) return;
    setMaterialsBusy(true); setError(null);
    try { await generateMaterialsStream({ lesson_plan: plan, activities: guide, assessment }, (event) => { if (event.type === "materials_completed" || event.type === "materials_reviewer_completed") setMaterials(event.materials); if (event.type === "materials_failure") setError(event.message); }, { mock: isMockMode, mockSpeed }); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "No fue posible preparar los materiales."); } finally { setMaterialsBusy(false); }
  }

  const headerMarkState: ClaraMarkState = screen === "generating" ? handoff ? "correcting" : "working" : "resting";
  return <main className="min-h-screen bg-[#f7f4ed]"><div className="mx-auto max-w-6xl px-5 py-8 sm:px-8 sm:py-12">
    <header className="no-print flex items-center gap-3"><ClaraMark state={headerMarkState} size="sm" /><div><p className="font-serif text-xl font-semibold text-stone-900">Clara</p><p className="text-xs text-stone-500">Compañera de planificación docente</p></div>{isMockMode && <span className="ml-auto rounded-full bg-[#fff0df] px-3 py-1 text-xs font-bold text-[#9a522b]">Vista previa</span>}</header>
    {screen === "request" && <div className="mx-auto mt-14 max-w-3xl"><p className="text-sm font-bold tracking-[.12em] text-[#c36c3e]">PLANIFICA CON CALMA</p><h1 className="mt-4 font-serif text-5xl text-stone-900">Una buena clase empieza con una intención clara.</h1><div className="mt-10">
      {isMockMode && <div className="mb-5 flex flex-wrap items-center gap-3 rounded-xl border border-[#ead3bd] bg-[#fff8f2] p-4 text-sm"><b className="text-[#82421f]">Modo vista previa</b><span className="text-stone-600">Reproduce el pack de agua sin usar la API.</span><label className="ml-auto flex items-center gap-2">Velocidad <select value={mockSpeed} onChange={(event) => setMockSpeed(event.target.value as MockSpeed)} className="rounded-md border border-stone-300 bg-white px-2 py-1"><option value="slow">Lenta</option><option value="normal">Normal</option><option value="fast">Rápida</option></select></label></div>}
      <LessonRequestForm onSubmit={start} />{error && <p className="mt-4 rounded-xl bg-red-50 p-4 text-sm text-red-800">{error}</p>}</div></div>}
    {screen === "generating" && <GenerationProgress planner={planner} designer={designer} assessment={evaluator} reviewer={reviewer} handoff={handoff} plan={plan} guide={guide} instrument={assessment} />}
    {screen === "results" && plan && guide && assessment && review && <>{isMockMode && <div className="no-print mt-8 flex justify-end"><button onClick={() => setScreen("request")} className="rounded-lg bg-[#195b4e] px-4 py-2 text-sm font-semibold text-white hover:bg-[#12463c]">Reproducir generación</button></div>}<TeachingPackResults plan={plan} guide={guide} assessment={assessment} review={review} materials={materials} onGenerateMaterials={createMaterials} materialsBusy={materialsBusy} /></>}
  </div></main>;
}

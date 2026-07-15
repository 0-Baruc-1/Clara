import { useEffect, useState } from "react";
import type {
  ActivityGuide,
  Assessment,
  LessonPlan,
  MaterialPack,
  ReviewFinding,
  ReviewReport,
} from "../types/teachingPack";
import { ResultSection } from "./ResultSection";

type EditablePack = {
  lesson_plan: LessonPlan;
  activities: ActivityGuide;
  assessment: Assessment;
  materials: MaterialPack | null;
};

const List = ({ items }: { items: string[] }) => (
  <ul className="space-y-2">
    {items.map((item, index) => (
      <li key={`${item}-${index}`}>• {item}</li>
    ))}
  </ul>
);
const printTarget = (target: "full" | "student" | "materials") => {
  document.body.dataset.printTarget = target;
  window.print();
  window.setTimeout(() => delete document.body.dataset.printTarget, 0);
};

function EditableText({
  value,
  onChange,
  label,
  multiline = false,
  className = "",
}: {
  value: string;
  onChange: (value: string) => void;
  label: string;
  multiline?: boolean;
  className?: string;
}) {
  const [editing, setEditing] = useState(false);
  if (editing)
    return (
      <textarea
        aria-label={label}
        autoFocus
        rows={multiline ? 3 : 1}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onBlur={() => setEditing(false)}
        className={`w-full resize-y rounded-md border border-[#c6d8d1] bg-white px-2 py-1 text-inherit leading-inherit outline-none ring-[#3b7969] focus:ring-2 ${className}`}
      />
    );
  return (
    <button
      type="button"
      aria-label={`Editar ${label}`}
      onClick={() => setEditing(true)}
      className={`group relative block w-full rounded-md text-left transition hover:bg-[#f0f6f2] focus:bg-[#f0f6f2] focus:outline-none ${className}`}
    >
      <span>{value || "Sin contenido"}</span>
      <span className="ml-2 whitespace-nowrap text-xs font-semibold text-[#3b7969] opacity-0 transition group-hover:opacity-100 group-focus:opacity-100">
        Editar
      </span>
    </button>
  );
}

function EditableList({
  items,
  onChange,
  label,
}: {
  items: string[];
  onChange: (items: string[]) => void;
  label: string;
}) {
  return (
    <ul className="space-y-2">
      {items.map((item, index) => (
        <li key={`${label}-${index}`}>
          <EditableText
            value={item}
            label={`${label} ${index + 1}`}
            multiline
            onChange={(value) =>
              onChange(
                items.map((current, itemIndex) =>
                  itemIndex === index ? value : current,
                ),
              )
            }
          />
        </li>
      ))}
    </ul>
  );
}

function ReviewNotes({
  findings,
  referenceFor,
  humanize,
}: {
  findings: ReviewFinding[];
  referenceFor: (artifactId: string) => string;
  humanize: (value: string) => string;
}) {
  if (!findings.length) return null;
  const tone = {
    bloqueante: "border-rose-300 bg-rose-50 text-rose-950",
    importante: "border-amber-300 bg-amber-50 text-amber-950",
    menor: "border-stone-300 bg-stone-50 text-stone-800",
  };
  return (
    <aside
      className="no-print mt-6 space-y-3"
      aria-label="Observaciones de revisión de Clara"
    >
      <p className="text-sm font-semibold text-stone-700">
        Observaciones de Clara sobre esta versión
      </p>
      {findings.map((finding) => (
        <article
          key={finding.id}
          className={`rounded-xl border-l-4 p-4 ${tone[finding.severity]}`}
        >
          <div className="flex flex-wrap gap-2 text-xs font-bold uppercase tracking-wide">
            <span>{finding.severity}</span>
            <span className="normal-case font-semibold tracking-normal">
              {referenceFor(finding.artifact_id)}
            </span>
          </div>
          <p className="mt-2 font-medium">{humanize(finding.description)}</p>
          <p className="mt-2 text-sm">
            <b>Sugerencia:</b> {humanize(finding.suggested_correction)}
          </p>
        </article>
      ))}
    </aside>
  );
}

function AssessmentArea({
  assessment,
  findings,
  itemLabel,
  humanize,
  updateItem,
  onAssessmentChange,
}: {
  assessment: Assessment;
  findings: ReviewFinding[];
  itemLabel: (id: string) => string;
  humanize: (value: string) => string;
  updateItem: (
    id: string,
    update: (item: Assessment["items"][number]) => Assessment["items"][number],
  ) => void;
  onAssessmentChange: (assessment: Assessment) => void;
}) {
  const cognitiveLevels = [
    ...new Set(
      assessment.specification_table.flatMap((row) => row.cognitive_levels),
    ),
  ];
  return (
    <section id="evaluacion" className="print-break scroll-mt-28">
      <ResultSection
        eyebrow="Instrumento de evaluación"
        title={assessment.title}
      >
        <div className="flex flex-wrap items-baseline justify-between gap-2">
            <p>
              {assessment.suggested_application_minutes} min ·{" "}
              {assessment.total_points} puntos
            </p>
            <p className="text-xs font-semibold uppercase tracking-wide text-[#3b7969]">
              {assessment.specification_table.length} objetivos ·{" "}
              {[
                ...new Set(
                  assessment.specification_table.flatMap(
                    (row) => row.cognitive_levels,
                  ),
                ),
              ].join(" · ")}
            </p>
          </div>
        <div className="mt-5 overflow-x-auto rounded-xl border border-stone-200">
          <table className="specification-table w-full min-w-[640px] border-collapse text-left text-sm">
            <caption className="caption-top px-4 py-3 text-left font-semibold text-stone-800">
              Tabla de especificaciones
            </caption>
            <thead>
              <tr>
                <th scope="col">Objetivo de aprendizaje</th>
                <th scope="col">Ítems</th>
                <th scope="col" className="text-right">
                  Puntaje
                </th>
                <th scope="col">Nivel cognitivo</th>
              </tr>
            </thead>
            <tbody>
              {assessment.specification_table.map((row) => (
                <tr key={row.learning_objective}>
                  <td>{row.learning_objective}</td>
                  <td>{row.item_ids.map(itemLabel).join(", ")}</td>
                  <td className="text-right font-semibold">
                    {row.total_points} pts
                  </td>
                  <td>{row.cognitive_levels.join(", ")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {assessment.items.map((item, itemIndex) => (
          <article key={item.id} className="mt-5 rounded-xl bg-[#fbfaf6] p-4">
            <p>
              <b>{itemLabel(item.id)}.</b>{" "}
              <EditableText
                value={item.question}
                multiline
                label={`enunciado ${itemIndex + 1}`}
                onChange={(question) =>
                  updateItem(item.id, (current) => ({ ...current, question }))
                }
              />{" "}
              <span>({item.points} pts)</span>
            </p>
            {item.options.map((option, optionIndex) => (
              <p
                key={option.label}
                className={
                  option.label === item.correct_option_label
                    ? "font-bold text-[#195b4e]"
                    : ""
                }
              >
                {option.label}.{" "}
                <EditableText
                  value={option.text}
                  label={`alternativa ${option.label} del ítem ${itemIndex + 1}`}
                  onChange={(text) =>
                    updateItem(item.id, (current) => ({
                      ...current,
                      options: current.options.map(
                        (candidate, candidateIndex) =>
                          candidateIndex === optionIndex
                            ? { ...candidate, text }
                            : candidate,
                      ),
                    }))
                  }
                />
                {option.label === item.correct_option_label && " ✓"}
              </p>
            ))}
            {item.correct_option_label && (
              <p>
                <b>Alternativa correcta:</b> {item.correct_option_label}
              </p>
            )}
            <p>
              <b>Criterio / respuesta esperada:</b>{" "}
              <EditableText
                value={item.expected_answer}
                multiline
                label={`respuesta esperada ítem ${itemIndex + 1}`}
                onChange={(expected_answer) =>
                  updateItem(item.id, (current) => ({
                    ...current,
                    expected_answer,
                  }))
                }
              />
            </p>
          </article>
        ))}
        {assessment.rubric.map((criterion, criterionIndex) => (
          <article
            key={criterion.criterion}
            className="mt-4 rounded-xl border p-4"
          >
            <EditableText
              value={criterion.criterion}
              label={`criterio de rúbrica ${criterionIndex + 1}`}
              className="font-semibold"
              onChange={(criterionName) =>
                onAssessmentChange({
                  ...assessment,
                  rubric: assessment.rubric.map((current, index) =>
                    index === criterionIndex
                      ? { ...current, criterion: criterionName }
                      : current,
                  ),
                })
              }
            />
            <p>
              Logrado:{" "}
              <EditableText
                value={criterion.levels.logrado}
                multiline
                label={`logrado ${criterionIndex + 1}`}
                onChange={(logrado) =>
                  onAssessmentChange({
                    ...assessment,
                    rubric: assessment.rubric.map((current, index) =>
                      index === criterionIndex
                        ? { ...current, levels: { ...current.levels, logrado } }
                        : current,
                    ),
                  })
                }
              />
            </p>
            <p>
              En proceso:{" "}
              <EditableText
                value={criterion.levels.en_proceso}
                multiline
                label={`en proceso ${criterionIndex + 1}`}
                onChange={(en_proceso) =>
                  onAssessmentChange({
                    ...assessment,
                    rubric: assessment.rubric.map((current, index) =>
                      index === criterionIndex
                        ? {
                            ...current,
                            levels: { ...current.levels, en_proceso },
                          }
                        : current,
                    ),
                  })
                }
              />
            </p>
            <p>
              Requiere apoyo:{" "}
              <EditableText
                value={criterion.levels.requiere_apoyo}
                multiline
                label={`requiere apoyo ${criterionIndex + 1}`}
                onChange={(requiere_apoyo) =>
                  onAssessmentChange({
                    ...assessment,
                    rubric: assessment.rubric.map((current, index) =>
                      index === criterionIndex
                        ? {
                            ...current,
                            levels: { ...current.levels, requiere_apoyo },
                          }
                        : current,
                    ),
                  })
                }
              />
            </p>
          </article>
        ))}
        <ReviewNotes
          findings={findings}
          referenceFor={(id) => itemLabel(id)}
          humanize={humanize}
        />
      </ResultSection>
    </section>
  );
}

function derivedGuide(guide: ActivityGuide): ActivityGuide {
  return {
    ...guide,
    materials_summary: [
      ...new Set(
        guide.activities.flatMap((activity) =>
          activity.materials.map((material) => material.trim()).filter(Boolean),
        ),
      ),
    ],
  };
}

function derivedAssessment(assessment: Assessment): Assessment {
  const byObjective = new Map<
    string,
    { item_ids: string[]; total_points: number; cognitive_levels: string[] }
  >();
  assessment.items.forEach((item) => {
    const current = byObjective.get(item.learning_objective) ?? {
      item_ids: [],
      total_points: 0,
      cognitive_levels: [],
    };
    current.item_ids.push(item.id);
    current.total_points += item.points;
    if (!current.cognitive_levels.includes(item.cognitive_level))
      current.cognitive_levels.push(item.cognitive_level);
    byObjective.set(item.learning_objective, current);
  });
  return {
    ...assessment,
    total_points: assessment.items.reduce(
      (total, item) => total + item.points,
      0,
    ),
    specification_table: [...byObjective].map(([learning_objective, row]) => ({
      learning_objective,
      item_count: row.item_ids.length,
      ...row,
    })),
  };
}

function markdownFor(pack: EditablePack): string {
  const { lesson_plan: plan, activities: guide, assessment, materials } = pack;
  const lines = [
    `# ${plan.title}`,
    "",
    `**${plan.subject} · ${plan.grade_level} · ${plan.duration_minutes} min**`,
    "",
    "## Objetivos curriculares",
    ...plan.curriculum_alignment.objectives.flatMap((objective) => [
      `- **${objective.code}** — ${objective.description}`,
    ]),
    "",
    "## Objetivos de aprendizaje",
    ...plan.learning_objectives.map((objective) => `- ${objective}`),
    "",
    "## Plan de clase",
    ...plan.stages.flatMap((stage) => [
      `### ${stage.name} (${stage.duration_minutes} min)`,
      stage.purpose,
      "",
    ]),
    "## Actividades",
  ];
  guide.activities.forEach((activity) =>
    lines.push(
      `### ${activity.stage_name}: ${activity.title} (${activity.duration_minutes} min, ${activity.grouping})`,
      ...activity.teacher_instructions.map((instruction) => `- ${instruction}`),
      `**Producto esperado:** ${activity.expected_student_output}`,
      `**Apoyo:** ${activity.differentiation.support}`,
      `**Extensión:** ${activity.differentiation.extension}`,
      `**Materiales:** ${activity.materials.join(", ")}`,
      "",
    ),
  );
  lines.push(
    "## Instrumento de evaluación",
    "",
    "### Tabla de especificaciones",
    "| Objetivo de aprendizaje | Ítems | Puntaje | Nivel cognitivo |",
    "| --- | --- | ---: | --- |",
    ...assessment.specification_table.map((row) => {
      const itemLabels = row.item_ids.map((id) => {
        const index = assessment.items.findIndex((item) => item.id === id);
        return index >= 0 ? `Ítem ${index + 1}` : "Ítem";
      });
      return `| ${row.learning_objective} | ${itemLabels.join(", ")} | ${row.total_points} pts | ${row.cognitive_levels.join(", ")} |`;
    }),
    "",
  );
  lines.push(
    ...assessment.items.flatMap((item, index) => [
      `### Ítem ${index + 1} · ${item.points} pts`,
      item.question,
      ...item.options.map((option) => `- ${option.label}. ${option.text}`),
      `**Respuesta esperada:** ${item.expected_answer}`,
      "",
    ]),
    "## Rúbrica",
  );
  assessment.rubric.forEach((criterion) =>
    lines.push(
      `### ${criterion.criterion}`,
      `- Logrado: ${criterion.levels.logrado}`,
      `- En proceso: ${criterion.levels.en_proceso}`,
      `- Requiere apoyo: ${criterion.levels.requiere_apoyo}`,
      "",
    ),
  );
  if (materials) {
    lines.push("## Materiales imprimibles");
    materials.materials.forEach((material) =>
      lines.push(
        `### ${material.title}`,
        ...material.student_instructions.map(
          (instruction) => `- ${instruction}`,
        ),
        ...material.content.flatMap((block) => [
          block.title ?? "",
          block.content ?? "",
          ...block.cards.flatMap((card) => [
            `- ${card.front ?? ""}: ${card.back ?? ""}`,
          ]),
        ]),
        "",
      ),
    );
  }
  return lines
    .filter((line, index, all) => line || all[index - 1] !== "")
    .join("\n");
}

export function TeachingPackResults({
  plan,
  guide,
  assessment,
  review,
  materials,
  onPlanChange,
  onGuideChange,
  onAssessmentChange,
  onMaterialsChange,
  onGenerateMaterials,
  materialsBusy,
  onReviewEdits,
  editReviewBusy,
  editReviewError,
  editReviewStatus,
  hasEdits,
  onReplay,
}: {
  plan: LessonPlan;
  guide: ActivityGuide;
  assessment: Assessment;
  review: ReviewReport;
  materials: MaterialPack | null;
  onPlanChange: (plan: LessonPlan) => void;
  onGuideChange: (guide: ActivityGuide) => void;
  onAssessmentChange: (assessment: Assessment) => void;
  onMaterialsChange: (materials: MaterialPack) => void;
  onGenerateMaterials: (pack: EditablePack) => void;
  materialsBusy: boolean;
  onReviewEdits: (pack: EditablePack) => void;
  editReviewBusy: boolean;
  editReviewError: string | null;
  editReviewStatus: string | null;
  hasEdits: boolean;
  onReplay?: () => void;
}) {
  const [copyState, setCopyState] = useState<"idle" | "copied">("idle");
  const [activeSection, setActiveSection] = useState("plan");
  const grouped = guide.activities.reduce<
    Record<string, typeof guide.activities>
  >((all, activity) => {
    (all[activity.stage_name] ??= []).push(activity);
    return all;
  }, {});
  const findingsFor = (agent: ReviewFinding["responsible_agent"]) =>
    review.findings.filter((finding) => finding.responsible_agent === agent);
  const itemLabel = (id: string) => {
    const index = assessment.items.findIndex((item) => item.id === id);
    if (index >= 0) return `Ítem ${index + 1}`;
    const match = /^item-(\d+)$/i.exec(id);
    return match ? `Ítem ${match[1]}` : "Ítem";
  };
  const artifactLabel = (id: string) => {
    const activity = guide.activities.find((entry) => entry.id === id);
    if (activity) return `Actividad: ${activity.title}`;
    const material = materials?.materials.find((entry) => entry.id === id);
    if (material) return `Material: ${material.title}`;
    if (/^activity-/i.test(id) || /^act-/i.test(id)) return "Actividad";
    if (/^material-/i.test(id) || /^mat-/i.test(id)) return "Material imprimible";
    return itemLabel(id);
  };
  const humanize = (value: string) =>
    [
      ...assessment.items.map((item) => [item.id, itemLabel(item.id)] as const),
      ...guide.activities.map(
        (activity) => [activity.id, `Actividad: ${activity.title}`] as const,
      ),
      ...(materials?.materials.map(
        (material) => [material.id, `Material: ${material.title}`] as const,
      ) ?? []),
    ]
      .reduce((text, [raw, label]) => text.split(raw).join(label), value)
      .replace(/\bitem-(\d+)\b/gi, "Ítem $1")
      .replace(/\b(?:activity|act)-[\w-]+\b/gi, "Actividad")
      .replace(/\b(?:material|mat)-[\w-]+\b/gi, "Material imprimible");
  const passed = review.status === "clean" && !review.findings.length;
  const alignment = {
    aligned: {
      label: "Objetivos curriculares verificados",
      detail: "Clara encontró y verificó OA oficiales para esta clase.",
    },
    partial: {
      label: "Cobertura curricular parcial",
      detail:
        "Clara encontró referencias curriculares, pero no cubren completamente la solicitud.",
    },
    not_found: {
      label: "Sin cobertura curricular encontrada",
      detail:
        "Clara no encontró OA disponibles para esta asignatura y nivel; por eso no atribuye códigos curriculares.",
    },
  }[plan.curriculum_alignment.status];
  const nav = [
    ["plan", "Plan"],
    ["actividades", "Actividades"],
    ["evaluacion", "Instrumento"],
    ...(materials ? [["materiales", "Materiales"]] : []),
  ] as [string, string][];
  useEffect(() => {
    const sections = nav
      .map(([id]) => document.getElementById(id))
      .filter((section): section is HTMLElement => section !== null);
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((left, right) => left.boundingClientRect.top - right.boundingClientRect.top);
        if (visible[0]) setActiveSection(visible[0].target.id);
      },
      { rootMargin: "-18% 0px -70% 0px", threshold: 0 },
    );
    sections.forEach((section) => observer.observe(section));
    return () => observer.disconnect();
  }, [materials]);
  const pack = (): EditablePack => ({
    lesson_plan: plan,
    activities: guide,
    assessment,
    materials,
  });
  const updateActivity = (
    id: string,
    update: (
      activity: (typeof guide.activities)[number],
    ) => (typeof guide.activities)[number],
  ) =>
    onGuideChange(
      derivedGuide({
        ...guide,
        activities: guide.activities.map((activity) =>
          activity.id === id ? update(activity) : activity,
        ),
      }),
    );
  const updateItem = (
    id: string,
    update: (
      item: (typeof assessment.items)[number],
    ) => (typeof assessment.items)[number],
  ) =>
    onAssessmentChange(
      derivedAssessment({
        ...assessment,
        items: assessment.items.map((item) =>
          item.id === id ? update(item) : item,
        ),
      }),
    );
  const copyMarkdown = async () => {
    await navigator.clipboard.writeText(markdownFor(pack()));
    setCopyState("copied");
    window.setTimeout(() => setCopyState("idle"), 1800);
  };
  const downloadMarkdown = () => {
    const url = URL.createObjectURL(
      new Blob([markdownFor(pack())], { type: "text/markdown;charset=utf-8" }),
    );
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "pack-clara.md";
    anchor.click();
    URL.revokeObjectURL(url);
  };
  return (
    <div className="teaching-pack mt-12 space-y-10">
      <header className="border-b border-stone-200 pb-7">
        <p className="text-sm font-semibold uppercase tracking-[.16em] text-[#3b7969]">
          Pack de enseñanza
        </p>
        <EditableText
          value={plan.title}
          label="título de la clase"
          className="mt-2 font-serif text-4xl text-stone-900"
          onChange={(title) => onPlanChange({ ...plan, title })}
        />
        <div
          className={`mt-4 max-w-2xl rounded-xl px-4 py-3 text-sm ${passed ? "bg-emerald-50 text-emerald-900" : "bg-amber-50 text-amber-950"}`}
        >
          <b>
            {passed
              ? "Revisión de coherencia superada"
              : "Clara revisó el pack con transparencia"}
          </b>
          <p className="mt-1">
            {passed
              ? "Plan, actividades y evaluación fueron revisados en conjunto antes de llegar a ti."
              : "Estas observaciones se refieren al material de Clara, no a tu solicitud."}
          </p>
        </div>
      </header>
      <div className="no-print sticky top-3 z-20 rounded-2xl border border-stone-200 bg-[#fffcf7]/95 p-3 shadow-sm backdrop-blur">
        <div className="flex flex-wrap items-center justify-end gap-2">
          <details className="relative">
            <summary className="cursor-pointer list-none rounded-lg border border-stone-200 bg-white px-3 py-2 text-sm font-semibold text-stone-700 hover:bg-stone-50">
              Exportar
            </summary>
            <div className="absolute right-0 z-30 mt-2 w-56 rounded-xl border border-stone-200 bg-white p-2 shadow-lg">
              <p className="px-2 py-1 text-xs font-bold uppercase tracking-wide text-stone-500">Imprimir</p>
              <button onClick={() => printTarget("full")} className="block w-full rounded-lg px-3 py-2 text-left text-sm hover:bg-stone-50">Pack completo</button>
              <button onClick={() => printTarget("student")} className="block w-full rounded-lg px-3 py-2 text-left text-sm hover:bg-stone-50">Evaluación para estudiantes</button>
              {materials && <button onClick={() => printTarget("materials")} className="block w-full rounded-lg px-3 py-2 text-left text-sm hover:bg-stone-50">Materiales imprimibles</button>}
              <div className="my-1 border-t border-stone-100" />
              <p className="px-2 py-1 text-xs font-bold uppercase tracking-wide text-stone-500">Markdown</p>
              <button onClick={copyMarkdown} className="block w-full rounded-lg px-3 py-2 text-left text-sm hover:bg-stone-50">{copyState === "copied" ? "Copiado" : "Copiar Markdown"}</button>
              <button onClick={downloadMarkdown} className="block w-full rounded-lg px-3 py-2 text-left text-sm hover:bg-stone-50">Descargar .md</button>
            </div>
          </details>
          <button
            disabled={materialsBusy || !!materials}
            onClick={() => onGenerateMaterials(pack())}
            className="rounded-lg bg-[#195b4e] px-3 py-2 text-sm font-semibold text-white disabled:opacity-60"
          >
            {materials ? "Materiales listos" : materialsBusy ? "Preparando materiales…" : "Generar materiales"}
          </button>
          {(hasEdits || editReviewBusy) && <button
            disabled={editReviewBusy}
            onClick={() => onReviewEdits(pack())}
            className="rounded-lg bg-[#c36c3e] px-3 py-2 text-sm font-semibold text-white disabled:opacity-50"
          >
            {editReviewBusy ? "Revisando cambios…" : "Revisar mis cambios"}
          </button>}
        </div>
        <details className="mt-3 rounded-xl bg-white/70 p-2 lg:hidden">
          <summary className="cursor-pointer px-2 py-1 text-sm font-semibold text-stone-700">Índice del pack</summary>
          <nav className="mt-2 grid grid-cols-2 gap-1" aria-label="Secciones del pack">
            {nav.map(([id, label]) => <a key={id} href={`#${id}`} aria-current={activeSection === id ? "location" : undefined} className={`rounded-lg px-3 py-2 text-sm font-semibold ${activeSection === id ? "bg-[#edf5f0] text-[#195b4e]" : "text-stone-600 hover:bg-stone-100"}`}>{label}</a>)}
          </nav>
        </details>
        {hasEdits && (
          <p className="mt-2 text-xs text-stone-500">
            Tus cambios están en esta sesión y se incluyen al imprimir o
            exportar.
          </p>
        )}
        {editReviewError && (
          <p className="mt-2 rounded-lg bg-rose-50 p-2 text-sm text-rose-900">
            {editReviewError}
          </p>
        )}
        {onReplay && <button onClick={onReplay} className="mt-3 text-xs font-semibold text-stone-400 underline hover:text-stone-600">Vista previa · reproducir</button>}
      </div>
      <div className="lg:grid lg:grid-cols-[11rem_minmax(0,1fr)] lg:gap-10">
      <aside className="no-print sticky top-28 hidden h-fit self-start lg:block">
        <p className="px-3 text-xs font-bold uppercase tracking-[.14em] text-stone-400">Índice del pack</p>
        <nav className="mt-3 space-y-1" aria-label="Secciones del pack">
          {nav.map(([id, label]) => <a key={id} href={`#${id}`} aria-current={activeSection === id ? "location" : undefined} className={`block rounded-lg px-3 py-2 text-sm font-semibold transition ${activeSection === id ? "bg-[#edf5f0] text-[#195b4e]" : "text-stone-600 hover:bg-white"}`}>{label}</a>)}
        </nav>
      </aside>
      <div className="min-w-0 space-y-10">
      {editReviewStatus && (
        <p className="no-print rounded-xl bg-[#edf5f0] px-4 py-3 text-sm font-medium text-[#195b4e]">
          {editReviewStatus}
        </p>
      )}
      <section id="plan" className="scroll-mt-28">
        <ResultSection
          eyebrow="Plan de clase"
          title="Propósito y ruta de aprendizaje"
        >
          <p>
            {plan.subject} · {plan.grade_level} · {plan.duration_minutes} min
          </p>
          <div className="mt-5 rounded-xl bg-emerald-50 p-4">
            <b>{alignment.label}</b>
            <p className="mt-1 text-sm">{alignment.detail}</p>
            {plan.curriculum_alignment.objectives.map((objective, index) => (
              <p
                key={`${objective.code}-${index}`}
                className="mt-2 flex flex-wrap items-start gap-1"
              >
                <span className="w-28 font-bold">
                  <EditableText
                    value={objective.code}
                    label={`código OA ${index + 1}`}
                    onChange={(code) =>
                      onPlanChange({
                        ...plan,
                        curriculum_alignment: {
                          ...plan.curriculum_alignment,
                          objectives: plan.curriculum_alignment.objectives.map(
                            (current, objectiveIndex) =>
                              objectiveIndex === index
                                ? { ...current, code }
                                : current,
                          ),
                        },
                      })
                    }
                  />
                </span>
                <span className="min-w-56 flex-1">
                  <EditableText
                    value={objective.description}
                    multiline
                    label={`descripción OA ${index + 1}`}
                    onChange={(description) =>
                      onPlanChange({
                        ...plan,
                        curriculum_alignment: {
                          ...plan.curriculum_alignment,
                          objectives: plan.curriculum_alignment.objectives.map(
                            (current, objectiveIndex) =>
                              objectiveIndex === index
                                ? { ...current, description }
                                : current,
                          ),
                        },
                      })
                    }
                  />
                </span>
              </p>
            ))}
            <List items={plan.curriculum_alignment.notes} />
          </div>
          <div className="mt-5">
            <EditableList
              items={plan.learning_objectives}
              label="objetivo de aprendizaje"
              onChange={(learning_objectives) =>
                onPlanChange({ ...plan, learning_objectives })
              }
            />
          </div>
          <div className="mt-6 grid gap-3 sm:grid-cols-2">
            {plan.stages.map((stage, index) => (
              <article
                key={stage.name}
                className="rounded-xl border border-stone-200 bg-[#fbfaf6] p-4"
              >
                <p className="text-xs font-bold uppercase tracking-wide text-[#3b7969]">
                  {stage.duration_minutes} min
                </p>
                <b>{stage.name}</b>
                <EditableText
                  value={stage.purpose}
                  multiline
                  label={`propósito de ${stage.name}`}
                  className="mt-1 text-sm"
                  onChange={(purpose) =>
                    onPlanChange({
                      ...plan,
                      stages: plan.stages.map((current, stageIndex) =>
                        stageIndex === index
                          ? { ...current, purpose }
                          : current,
                      ),
                    })
                  }
                />
              </article>
            ))}
          </div>
          <ReviewNotes
            findings={findingsFor("planner")}
            referenceFor={artifactLabel}
            humanize={humanize}
          />
        </ResultSection>
      </section>
      <section id="actividades" className="print-break scroll-mt-28">
        <ResultSection eyebrow="Actividades de aula" title={guide.title}>
          {plan.stages.map((stage) => (
            <section key={stage.name} className="activity-stage mt-8">
              <div className="activity-stage__heading">
                <p>Etapa de la clase · {stage.duration_minutes} min</p>
                <h3>{stage.name}</h3>
                <span>{stage.purpose}</span>
              </div>
              {(grouped[stage.name] ?? []).map((activity, activityIndex) => (
                <article
                  key={activity.id}
                  className="mt-4 rounded-xl bg-[#fbfaf6] p-4"
                >
                  <EditableText
                    value={activity.title}
                    label={`título de actividad ${activityIndex + 1}`}
                    className="font-semibold"
                    onChange={(title) =>
                      updateActivity(activity.id, (current) => ({
                        ...current,
                        title,
                      }))
                    }
                  />
                  <p className="mt-1 text-sm text-stone-500">
                    {activity.duration_minutes} min · {activity.grouping}
                  </p>
                  <div className="mt-3">
                    <EditableList
                      items={activity.teacher_instructions}
                      label={`instrucción de actividad ${activityIndex + 1}`}
                      onChange={(teacher_instructions) =>
                        updateActivity(activity.id, (current) => ({
                          ...current,
                          teacher_instructions,
                        }))
                      }
                    />
                  </div>
                  <p className="mt-3">
                    <b>Producto:</b>{" "}
                    <EditableText
                      value={activity.expected_student_output}
                      multiline
                      label={`producto de actividad ${activityIndex + 1}`}
                      onChange={(expected_student_output) =>
                        updateActivity(activity.id, (current) => ({
                          ...current,
                          expected_student_output,
                        }))
                      }
                    />
                  </p>
                  <p>
                    <b>Materiales:</b>{" "}
                    <EditableText
                      value={activity.materials.join(", ")}
                      label={`materiales de actividad ${activityIndex + 1}`}
                      onChange={(materialsText) =>
                        updateActivity(activity.id, (current) => ({
                          ...current,
                          materials: materialsText
                            .split(",")
                            .map((value) => value.trim())
                            .filter(Boolean),
                        }))
                      }
                    />
                  </p>
                  <p>
                    <b>Apoyo:</b>{" "}
                    <EditableText
                      value={activity.differentiation.support}
                      multiline
                      label={`apoyo de actividad ${activityIndex + 1}`}
                      onChange={(support) =>
                        updateActivity(activity.id, (current) => ({
                          ...current,
                          differentiation: {
                            ...current.differentiation,
                            support,
                          },
                        }))
                      }
                    />
                  </p>
                  <p>
                    <b>Extensión:</b>{" "}
                    <EditableText
                      value={activity.differentiation.extension}
                      multiline
                      label={`extensión de actividad ${activityIndex + 1}`}
                      onChange={(extension) =>
                        updateActivity(activity.id, (current) => ({
                          ...current,
                          differentiation: {
                            ...current.differentiation,
                            extension,
                          },
                        }))
                      }
                    />
                  </p>
                </article>
              ))}
            </section>
          ))}
          <ReviewNotes
            findings={findingsFor("designer")}
            referenceFor={artifactLabel}
            humanize={humanize}
          />
        </ResultSection>
      </section>
      <section id="evaluacion" className="print-break scroll-mt-28">
        <ResultSection
          eyebrow="Instrumento de evaluación"
          title={assessment.title}
        >
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <p>
              {assessment.suggested_application_minutes} min ·{" "}
              {assessment.total_points} puntos
            </p>
            <p className="text-xs font-semibold uppercase tracking-wide text-[#3b7969]">
              {assessment.specification_table.length} objetivos ·{" "}
              {[
                ...new Set(
                  assessment.specification_table.flatMap(
                    (row) => row.cognitive_levels,
                  ),
                ),
              ].join(" · ")}
            </p>
          </div>
          <div className="mt-5 overflow-x-auto rounded-xl border border-stone-200">
            <table className="specification-table w-full min-w-[640px] border-collapse text-left text-sm">
              <caption className="caption-top px-4 py-3 text-left font-semibold text-stone-800">
                Tabla de especificaciones
              </caption>
              <thead>
                <tr>
                  <th scope="col">Objetivo de aprendizaje</th>
                  <th scope="col">Ítems</th>
                  <th scope="col" className="text-right">
                    Puntaje
                  </th>
                  <th scope="col">Nivel cognitivo</th>
                </tr>
              </thead>
              <tbody>
                {assessment.specification_table.map((row) => (
                  <tr key={row.learning_objective}>
                    <td>{row.learning_objective}</td>
                    <td>{row.item_ids.map(itemLabel).join(", ")}</td>
                    <td className="text-right font-semibold">
                      {row.total_points} pts
                    </td>
                    <td>{row.cognitive_levels.join(", ")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {assessment.items.map((item, itemIndex) => (
            <article key={item.id} className="mt-5 rounded-xl bg-[#fbfaf6] p-4">
              <p>
                <b>{itemLabel(item.id)}.</b>{" "}
                <EditableText
                  value={item.question}
                  multiline
                  label={`enunciado del ítem ${itemIndex + 1}`}
                  onChange={(question) =>
                    updateItem(item.id, (current) => ({ ...current, question }))
                  }
                />{" "}
                <span>({item.points} pts)</span>
              </p>
              {item.options.map((option, optionIndex) => (
                <p
                  key={option.label}
                  className={
                    option.label === item.correct_option_label
                      ? "font-bold text-[#195b4e]"
                      : ""
                  }
                >
                  {option.label}.{" "}
                  <EditableText
                    value={option.text}
                    label={`alternativa ${option.label} del ítem ${itemIndex + 1}`}
                    onChange={(text) =>
                      updateItem(item.id, (current) => ({
                        ...current,
                        options: current.options.map(
                          (candidate, candidateIndex) =>
                            candidateIndex === optionIndex
                              ? { ...candidate, text }
                              : candidate,
                        ),
                      }))
                    }
                  />
                  {option.label === item.correct_option_label && " ✓"}
                </p>
              ))}
              {item.correct_option_label && (
                <p>
                  <b>Alternativa correcta:</b> {item.correct_option_label}
                </p>
              )}
              <p>
                <b>Criterio / respuesta esperada:</b>{" "}
                <EditableText
                  value={item.expected_answer}
                  multiline
                  label={`respuesta esperada del ítem ${itemIndex + 1}`}
                  onChange={(expected_answer) =>
                    updateItem(item.id, (current) => ({
                      ...current,
                      expected_answer,
                    }))
                  }
                />
              </p>
            </article>
          ))}
          {assessment.rubric.map((criterion, criterionIndex) => (
            <article
              key={criterion.criterion}
              className="mt-4 rounded-xl border p-4"
            >
              <EditableText
                value={criterion.criterion}
                label={`criterio de rúbrica ${criterionIndex + 1}`}
                className="font-semibold"
                onChange={(criterionName) =>
                  onAssessmentChange({
                    ...assessment,
                    rubric: assessment.rubric.map((current, index) =>
                      index === criterionIndex
                        ? { ...current, criterion: criterionName }
                        : current,
                    ),
                  })
                }
              />
              <p>
                Logrado:{" "}
                <EditableText
                  value={criterion.levels.logrado}
                  multiline
                  label={`logrado ${criterionIndex + 1}`}
                  onChange={(logrado) =>
                    onAssessmentChange({
                      ...assessment,
                      rubric: assessment.rubric.map((current, index) =>
                        index === criterionIndex
                          ? {
                              ...current,
                              levels: { ...current.levels, logrado },
                            }
                          : current,
                      ),
                    })
                  }
                />
              </p>
              <p>
                En proceso:{" "}
                <EditableText
                  value={criterion.levels.en_proceso}
                  multiline
                  label={`en proceso ${criterionIndex + 1}`}
                  onChange={(en_proceso) =>
                    onAssessmentChange({
                      ...assessment,
                      rubric: assessment.rubric.map((current, index) =>
                        index === criterionIndex
                          ? {
                              ...current,
                              levels: { ...current.levels, en_proceso },
                            }
                          : current,
                      ),
                    })
                  }
                />
              </p>
              <p>
                Requiere apoyo:{" "}
                <EditableText
                  value={criterion.levels.requiere_apoyo}
                  multiline
                  label={`requiere apoyo ${criterionIndex + 1}`}
                  onChange={(requiere_apoyo) =>
                    onAssessmentChange({
                      ...assessment,
                      rubric: assessment.rubric.map((current, index) =>
                        index === criterionIndex
                          ? {
                              ...current,
                              levels: { ...current.levels, requiere_apoyo },
                            }
                          : current,
                      ),
                    })
                  }
                />
              </p>
            </article>
          ))}
          <ReviewNotes
            findings={findingsFor("assessment")}
            referenceFor={artifactLabel}
            humanize={humanize}
          />
        </ResultSection>
      </section>
      <section className="student-assessment print-student print-break">
        <ResultSection
          eyebrow="Evaluación para estudiantes"
          title={assessment.title}
        >
          <List items={assessment.instructions} />
          {assessment.items.map((item, itemIndex) => (
            <article key={item.id} className="mt-5">
              <p>
                <b>
                  Ítem {itemIndex + 1}. {item.question}
                </b>{" "}
                ({item.points} pts)
              </p>
              {item.options.map((option) => (
                <p key={option.label}>
                  ○ {option.label}. {option.text}
                </p>
              ))}
              {item.type !== "selección múltiple" && (
                <div className="mt-3 h-20 border-b border-stone-400" />
              )}
            </article>
          ))}
        </ResultSection>
      </section>
      {materials && (
        <section id="materiales" className="print-break scroll-mt-28">
          <ResultSection
            eyebrow="Materiales imprimibles"
            title={materials.title}
          >
            <div className="material-sheets">
              {materials.materials.map((material, materialIndex) => (
                <article
                  key={material.id}
                  className="material-sheet mt-5 rounded-xl border border-stone-200 p-6"
                >
                  <p className="text-xs font-bold uppercase tracking-wide text-[#3b7969]">
                    {material.source_material_label}
                  </p>
                  <EditableText
                    value={material.title}
                    label={`título del material ${materialIndex + 1}`}
                    className="mt-2 text-lg font-semibold"
                    onChange={(title) =>
                      onMaterialsChange({
                        ...materials,
                        materials: materials.materials.map((current, index) =>
                          index === materialIndex
                            ? { ...current, title }
                            : current,
                        ),
                      })
                    }
                  />
                  <div className="mt-3">
                    <EditableList
                      items={material.student_instructions}
                      label={`instrucción del material ${materialIndex + 1}`}
                      onChange={(student_instructions) =>
                        onMaterialsChange({
                          ...materials,
                          materials: materials.materials.map(
                            (current, index) =>
                              index === materialIndex
                                ? { ...current, student_instructions }
                                : current,
                          ),
                        })
                      }
                    />
                  </div>
                  {material.content.map((block, blockIndex) => (
                    <div key={blockIndex} className="mt-4">
                      {block.title !== undefined && (
                        <EditableText
                          value={block.title ?? ""}
                          label={`título bloque ${blockIndex + 1}`}
                          onChange={(title) =>
                            onMaterialsChange({
                              ...materials,
                              materials: materials.materials.map(
                                (current, index) =>
                                  index === materialIndex
                                    ? {
                                        ...current,
                                        content: current.content.map(
                                          (candidate, candidateIndex) =>
                                            candidateIndex === blockIndex
                                              ? { ...candidate, title }
                                              : candidate,
                                        ),
                                      }
                                    : current,
                              ),
                            })
                          }
                        />
                      )}
                      {block.content !== undefined && (
                        <EditableText
                          value={block.content ?? ""}
                          multiline
                          label={`contenido bloque ${blockIndex + 1}`}
                          onChange={(content) =>
                            onMaterialsChange({
                              ...materials,
                              materials: materials.materials.map(
                                (current, index) =>
                                  index === materialIndex
                                    ? {
                                        ...current,
                                        content: current.content.map(
                                          (candidate, candidateIndex) =>
                                            candidateIndex === blockIndex
                                              ? { ...candidate, content }
                                              : candidate,
                                        ),
                                      }
                                    : current,
                              ),
                            })
                          }
                        />
                      )}
                      {block.type === "tabla" && (
                        <table className="mt-2 w-full border-collapse text-sm">
                          <tbody>
                            <tr>
                              {block.columns.map((column, columnIndex) => (
                                <th
                                  key={columnIndex}
                                  className="border p-2 text-left"
                                >
                                  <EditableText
                                    value={column}
                                    label={`columna ${columnIndex + 1}`}
                                    onChange={(value) =>
                                      onMaterialsChange({
                                        ...materials,
                                        materials: materials.materials.map(
                                          (current, index) =>
                                            index === materialIndex
                                              ? {
                                                  ...current,
                                                  content: current.content.map(
                                                    (
                                                      candidate,
                                                      candidateIndex,
                                                    ) =>
                                                      candidateIndex ===
                                                      blockIndex
                                                        ? {
                                                            ...candidate,
                                                            columns:
                                                              candidate.columns.map(
                                                                (
                                                                  cell,
                                                                  cellIndex,
                                                                ) =>
                                                                  cellIndex ===
                                                                  columnIndex
                                                                    ? value
                                                                    : cell,
                                                              ),
                                                          }
                                                        : candidate,
                                                  ),
                                                }
                                              : current,
                                        ),
                                      })
                                    }
                                  />
                                </th>
                              ))}
                            </tr>
                            {block.rows.map((row, rowIndex) => (
                              <tr key={rowIndex}>
                                {row.map((cell, cellIndex) => (
                                  <td
                                    key={cellIndex}
                                    className="h-8 border p-2"
                                  >
                                    <EditableText
                                      value={cell}
                                      label={`celda ${rowIndex + 1}-${cellIndex + 1}`}
                                      onChange={(value) =>
                                        onMaterialsChange({
                                          ...materials,
                                          materials: materials.materials.map(
                                            (current, index) =>
                                              index === materialIndex
                                                ? {
                                                    ...current,
                                                    content:
                                                      current.content.map(
                                                        (
                                                          candidate,
                                                          candidateIndex,
                                                        ) =>
                                                          candidateIndex ===
                                                          blockIndex
                                                            ? {
                                                                ...candidate,
                                                                rows: candidate.rows.map(
                                                                  (
                                                                    candidateRow,
                                                                    candidateRowIndex,
                                                                  ) =>
                                                                    candidateRowIndex ===
                                                                    rowIndex
                                                                      ? candidateRow.map(
                                                                          (
                                                                            candidateCell,
                                                                            candidateCellIndex,
                                                                          ) =>
                                                                            candidateCellIndex ===
                                                                            cellIndex
                                                                              ? value
                                                                              : candidateCell,
                                                                        )
                                                                      : candidateRow,
                                                                ),
                                                              }
                                                            : candidate,
                                                      ),
                                                  }
                                                : current,
                                          ),
                                        })
                                      }
                                    />
                                  </td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      )}
                      {block.type === "tarjetas" && (
                        <div className="mt-2 grid grid-cols-2 gap-2">
                          {block.cards.map((card, cardIndex) => (
                            <div key={cardIndex} className="border p-3">
                              <EditableText
                                value={card.front ?? ""}
                                label={`frente tarjeta ${cardIndex + 1}`}
                                onChange={(front) =>
                                  onMaterialsChange({
                                    ...materials,
                                    materials: materials.materials.map(
                                      (current, index) =>
                                        index === materialIndex
                                          ? {
                                              ...current,
                                              content: current.content.map(
                                                (candidate, candidateIndex) =>
                                                  candidateIndex === blockIndex
                                                    ? {
                                                        ...candidate,
                                                        cards:
                                                          candidate.cards.map(
                                                            (
                                                              candidateCard,
                                                              candidateCardIndex,
                                                            ) =>
                                                              candidateCardIndex ===
                                                              cardIndex
                                                                ? {
                                                                    ...candidateCard,
                                                                    front,
                                                                  }
                                                                : candidateCard,
                                                          ),
                                                      }
                                                    : candidate,
                                              ),
                                            }
                                          : current,
                                    ),
                                  })
                                }
                              />
                              <hr className="my-2" />
                              <EditableText
                                value={card.back ?? ""}
                                label={`reverso tarjeta ${cardIndex + 1}`}
                                onChange={(back) =>
                                  onMaterialsChange({
                                    ...materials,
                                    materials: materials.materials.map(
                                      (current, index) =>
                                        index === materialIndex
                                          ? {
                                              ...current,
                                              content: current.content.map(
                                                (candidate, candidateIndex) =>
                                                  candidateIndex === blockIndex
                                                    ? {
                                                        ...candidate,
                                                        cards:
                                                          candidate.cards.map(
                                                            (
                                                              candidateCard,
                                                              candidateCardIndex,
                                                            ) =>
                                                              candidateCardIndex ===
                                                              cardIndex
                                                                ? {
                                                                    ...candidateCard,
                                                                    back,
                                                                  }
                                                                : candidateCard,
                                                          ),
                                                      }
                                                    : candidate,
                                              ),
                                            }
                                          : current,
                                    ),
                                  })
                                }
                              />
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </article>
              ))}
            </div>
            <ReviewNotes
              findings={findingsFor("materials")}
              referenceFor={artifactLabel}
              humanize={humanize}
            />
          </ResultSection>
        </section>
      )}
      </div>
    </div>
    </div>
  );
}

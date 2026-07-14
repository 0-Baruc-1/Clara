import type { LessonRequest, TeachingPack } from "../types/teachingPack";
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
export async function generateTeachingPack(request: LessonRequest): Promise<TeachingPack> {
  const response = await fetch(`${apiBaseUrl}/generate`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(request) });
  if (!response.ok) throw new Error("No pudimos generar el material. Inténtalo nuevamente.");
  return response.json() as Promise<TeachingPack>;
}


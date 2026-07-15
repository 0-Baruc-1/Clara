import type { ActivityGuide, Assessment, GenerationEvent, LessonPlan, LessonRequest } from "../types/teachingPack";
import { mockGenerationEvents } from "../fixtures/waterTeachingPack";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
export const isMockMode = import.meta.env.VITE_MOCK === "true" || new URLSearchParams(window.location.search).has("mock");
export type MockSpeed = "slow" | "normal" | "fast";
const mockDelays: Record<MockSpeed, number> = { slow: 1300, normal: 700, fast: 180 };
const wait = (milliseconds: number) => new Promise<void>((resolve) => window.setTimeout(resolve, milliseconds));

export async function generateTeachingPackStream(
  request: LessonRequest,
  onEvent: (event: GenerationEvent) => void,
  options: { mock?: boolean; mockSpeed?: MockSpeed } = {},
): Promise<void> {
  if (options.mock ?? isMockMode) {
    for (const event of mockGenerationEvents) {
      onEvent(event);
      await wait(mockDelays[options.mockSpeed ?? "normal"]);
    }
    return;
  }
  const response = await fetch(`${apiBaseUrl}/generate`, {
    method: "POST",
    headers: { Accept: "text/event-stream", "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!response.ok || !response.body) throw new Error("No pudimos iniciar la generación. Inténtalo nuevamente.");

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value, { stream: !done });
    const frames = buffer.split("\n\n");
    buffer = frames.pop() ?? "";
    for (const frame of frames) {
      const eventName = frame.match(/^event: (.+)$/m)?.[1];
      const data = frame.match(/^data: (.+)$/m)?.[1];
      if (!eventName || !data) continue;
      onEvent({ type: eventName, ...JSON.parse(data) } as GenerationEvent);
    }
    if (done) break;
  }
}

export async function generateMaterialsStream(pack: { lesson_plan: LessonPlan; activities: ActivityGuide; assessment: Assessment }, onEvent: (event: GenerationEvent) => void): Promise<void> {
  const response = await fetch(`${apiBaseUrl}/generate-materials`, { method: "POST", headers: { Accept: "text/event-stream", "Content-Type": "application/json" }, body: JSON.stringify(pack) });
  if (!response.ok || !response.body) throw new Error("No pudimos preparar los materiales.");
  const reader = response.body.getReader(); const decoder = new TextDecoder(); let buffer = "";
  while (true) { const { value, done } = await reader.read(); buffer += decoder.decode(value, { stream: !done }); const frames = buffer.split("\n\n"); buffer = frames.pop() ?? ""; for (const frame of frames) { const type = frame.match(/^event: (.+)$/m)?.[1]; const data = frame.match(/^data: (.+)$/m)?.[1]; if (type && data) onEvent({ type, ...JSON.parse(data) } as GenerationEvent); } if (done) break; }
}

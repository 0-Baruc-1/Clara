import type { GenerationEvent, LessonRequest } from "../types/teachingPack";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function generateTeachingPackStream(
  request: LessonRequest,
  onEvent: (event: GenerationEvent) => void,
): Promise<void> {
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

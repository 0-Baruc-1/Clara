const storageKey = "clara.teacher-session-id";

function newId() {
  return globalThis.crypto?.randomUUID?.() ?? `clara-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function teacherSessionId() {
  const existing = window.localStorage.getItem(storageKey);
  if (existing) return existing;
  const id = newId(); window.localStorage.setItem(storageKey, id); return id;
}

export function restoreTeacherSessionId(id: string) {
  const clean = id.trim();
  if (clean.length < 8) throw new Error("Ese identificador de sesión no parece válido.");
  window.localStorage.setItem(storageKey, clean);
  return clean;
}

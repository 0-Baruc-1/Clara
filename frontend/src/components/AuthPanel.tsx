import { useState } from "react";
import { useAuth } from "../auth/AuthProvider";

export function AuthPanel() {
  const { phase, user, role, error, signIn, signOut } = useAuth();
  const [open, setOpen] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  if (phase === "signed_in" && user && role) return <div className="ml-auto flex items-center gap-3 text-sm"><span className="hidden text-stone-600 sm:inline">{role === "teacher" ? "Docente" : "Estudiante"} · {user.email}</span><button onClick={() => void signOut()} className="rounded-lg border border-stone-200 bg-white px-3 py-2 font-semibold text-stone-700">Salir</button></div>;
  if (phase === "loading") return <p className="ml-auto text-sm text-stone-500">Verificando sesión…</p>;
  return <div className="ml-auto"><button onClick={() => setOpen((value) => !value)} className="rounded-lg border border-[#195b4e] bg-white px-3 py-2 text-sm font-semibold text-[#195b4e]">{phase === "expired" ? "Volver a iniciar sesión" : "Iniciar sesión"}</button>{open && <form onSubmit={async (event) => { event.preventDefault(); setBusy(true); setFormError(null); try { await signIn(email, password); setOpen(false); } catch (caught) { setFormError(caught instanceof Error ? caught.message : "No pudimos iniciar sesión."); } finally { setBusy(false); } }} className="absolute right-5 z-20 mt-2 w-80 rounded-2xl border border-stone-200 bg-white p-5 shadow-xl sm:right-8"><p className="font-serif text-xl text-stone-900">Entrar a Clara</p><p className="mt-1 text-sm text-stone-600">Usa la cuenta asignada a tu curso.</p><label className="field mt-4"><span>Correo</span><input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required /></label><label className="field mt-3"><span>Contraseña</span><input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required /></label>{(formError || error) && <p className="mt-3 text-sm text-rose-800">{formError || error}</p>}<button disabled={busy} className="mt-4 w-full rounded-lg bg-[#195b4e] px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50">{busy ? "Ingresando…" : "Iniciar sesión"}</button></form>}</div>;
}

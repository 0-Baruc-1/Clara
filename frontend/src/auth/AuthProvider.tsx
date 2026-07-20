import type { Session, User } from "@supabase/supabase-js";
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import type { ClaraRole } from "../types/studentSection";
import { supabase, supabaseConfigurationError } from "../lib/supabase";

type AuthPhase = "loading" | "signed_out" | "signed_in" | "expired" | "misconfigured";

type AuthContextValue = {
  phase: AuthPhase;
  session: Session | null;
  user: User | null;
  role: ClaraRole | null;
  error: string | null;
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  markRequestRejected: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

async function readOwnRole(userId: string): Promise<ClaraRole> {
  if (!supabase) throw new Error(supabaseConfigurationError ?? "Supabase no está disponible.");
  const { data, error } = await supabase
    .from("clara_user_roles")
    .select("role")
    .eq("user_id", userId)
    .maybeSingle();
  if (error) throw new Error("No pudimos verificar tu rol en Clara.");
  if (data?.role !== "teacher" && data?.role !== "student") {
    throw new Error("Tu cuenta no tiene un rol de Clara asignado. Pide a quien administra el curso que lo revise.");
  }
  return data.role;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [phase, setPhase] = useState<AuthPhase>(supabase ? "loading" : "misconfigured");
  const [session, setSession] = useState<Session | null>(null);
  const [role, setRole] = useState<ClaraRole | null>(null);
  const [error, setError] = useState<string | null>(supabaseConfigurationError);
  const [hadSession, setHadSession] = useState(false);

  const applySession = useCallback(async (next: Session | null) => {
    setSession(next);
    setRole(null);
    if (!next) {
      setPhase(hadSession ? "expired" : "signed_out");
      return;
    }
    setHadSession(true);
    try {
      const nextRole = await readOwnRole(next.user.id);
      setRole(nextRole);
      setError(null);
      setPhase("signed_in");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "No pudimos verificar tu acceso.");
      setPhase("signed_out");
    }
  }, [hadSession]);

  useEffect(() => {
    if (!supabase) return;
    let active = true;
    void supabase.auth.getSession().then(({ data, error: sessionError }) => {
      if (!active) return;
      if (sessionError) {
        setError("No pudimos recuperar tu sesión.");
        setPhase("signed_out");
        return;
      }
      void applySession(data.session);
    });
    const { data: listener } = supabase.auth.onAuthStateChange((_event, next) => {
      // Supabase recommends deferring database work outside this callback.
      // Role lookup starts on the next task, after Auth releases its lock.
      if (active) window.setTimeout(() => { if (active) void applySession(next); }, 0);
    });
    return () => { active = false; listener.subscription.unsubscribe(); };
  }, [applySession]);

  const signIn = useCallback(async (email: string, password: string) => {
    if (!supabase) throw new Error(supabaseConfigurationError ?? "Supabase no está disponible.");
    setPhase("loading");
    setError(null);
    const { data, error: signInError } = await supabase.auth.signInWithPassword({ email, password });
    if (signInError || !data.session) {
      setPhase("signed_out");
      throw new Error("No pudimos iniciar sesión. Revisa tu correo y contraseña.");
    }
    await applySession(data.session);
  }, [applySession]);

  const signOut = useCallback(async () => {
    if (supabase) await supabase.auth.signOut({ scope: "local" });
    setSession(null); setRole(null); setHadSession(false); setError(null); setPhase("signed_out");
  }, []);

  const markRequestRejected = useCallback(async () => {
    if (supabase) await supabase.auth.signOut({ scope: "local" });
    setSession(null); setRole(null); setError("Tu sesión fue rechazada o venció. Inicia sesión nuevamente."); setPhase("expired");
  }, []);

  const value = useMemo(() => ({ phase, session, user: session?.user ?? null, role, error, signIn, signOut, markRequestRejected }), [phase, session, role, error, signIn, signOut, markRequestRejected]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth debe usarse dentro de AuthProvider.");
  return value;
}

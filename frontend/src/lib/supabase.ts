import { createClient } from "@supabase/supabase-js";

const url = import.meta.env.VITE_SUPABASE_URL?.trim();
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY?.trim();

export const supabaseConfigurationError =
  !url || !anonKey
    ? "Falta configurar VITE_SUPABASE_URL y VITE_SUPABASE_ANON_KEY para iniciar sesión."
    : null;

// The anon key is intentionally browser-visible. It is not a service-role key;
// RLS remains the database authorization boundary for every browser query.
export const supabase =
  url && anonKey
    ? createClient(url, anonKey, {
        auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true },
      })
    : null;

export const demoClassId = import.meta.env.VITE_DEMO_CLASS_ID?.trim() || null;

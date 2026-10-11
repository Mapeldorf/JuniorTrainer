// Produccion (ver environment.development.ts para desarrollo local).
// La anon/publishable key es publica por diseno (Supabase la protege con
// Row Level Security), por eso va aqui y no como secreto.
export const environment = {
  production: true,
  supabaseUrl: 'https://uwgqxdfpkkbenmynwlmk.supabase.co',
  supabasePublishableKey: 'sb_publishable_jFF2fuXQIWriqw-u0YA1Ig_cGrQjTsi',
  apiUrl: 'http://localhost:8000',
};

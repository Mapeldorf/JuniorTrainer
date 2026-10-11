-- Corrige los avisos de seguridad del advisor tras la migracion 0001:
-- search_path fijo en las funciones y RPC no expuesta para las internas.

alter function public.block_exercise_requires_saved() set search_path = public;
alter function public.reject_update() set search_path = public;
alter function public.exercise_lock_after_saved() set search_path = public;
alter function public.set_updated_at() set search_path = public;

-- current_profile_role la llaman las policies RLS evaluadas como "authenticated",
-- asi que ese rol conserva EXECUTE; solo se cierra a anon (y al PUBLIC por defecto).
revoke execute on function public.current_profile_role() from public, anon;
grant execute on function public.current_profile_role() to authenticated;

-- handle_new_user solo la dispara el trigger on_auth_user_created; ningun rol
-- de API necesita invocarla directamente.
revoke execute on function public.handle_new_user() from public, anon, authenticated;

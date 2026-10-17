-- JuniorTrainer — eliminar-generaciones-por-revisar (tarea 1.1)
-- Las FK de exercise y repo_access_log hacia generation pasan a on delete
-- cascade, para que eliminar una generacion (DELETE /generations/{id})
-- borre en una sola sentencia atomica sus ejercicios candidatos y sus
-- registros de auditoria. Ver design.md - Decisions (D2). El endpoint solo
-- llega aqui cuando la generacion esta `ready` y ninguno de sus ejercicios
-- esta guardado (`saved = false`), asi que la cascada nunca toca el catalogo
-- de definitivos ni, por tanto, las FK de block_exercise/assignment_exercise.

alter table public.exercise
  drop constraint if exists exercise_generation_id_fkey;

alter table public.exercise
  add constraint exercise_generation_id_fkey
  foreign key (generation_id) references public.generation (id) on delete cascade;

alter table public.repo_access_log
  drop constraint if exists repo_access_log_generation_id_fkey;

alter table public.repo_access_log
  add constraint repo_access_log_generation_id_fkey
  foreign key (generation_id) references public.generation (id) on delete cascade;
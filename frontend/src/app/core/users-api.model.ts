/**
 * DTOs de `POST /users`, `GET /users` (capacidad `user-auth`, ya
 * implementada) y `GET /users/{id}/blocks` (capacidad `block-assignment`,
 * tarea 1.2 de backend de frontend-tech-lead-alumnos). Se replica a mano,
 * igual que el resto de `*-api.model.ts`.
 */
import { ExerciseProgress } from './blocks-api.model';

export interface StudentSummary {
  id: string;
  name: string;
  email: string;
}

/** Body de `POST /users` (tarea 3.1): invitar a un alumno nuevo. */
export interface InviteStudentRequest {
  name: string;
  email: string;
}

/** Respuesta de `POST /users`: el backend no devuelve un `StudentSummary`
 * completo (no hay `id`/`name` todavia, el alumno se crea al confirmar la
 * invitacion) -- solo confirma el email invitado (tasks.md - tarea 3.1). */
export interface InviteStudentResponse {
  email: string;
  status: string;
}

/** Una asignacion de un alumno, vista desde el alumno (tarea 3.1,
 * respuesta de `GET /users/{id}/blocks`): mismo detalle por ejercicio que
 * `StudentProgress` en blocks-api.model.ts, pero el dato que identifica
 * cada fila es el bloque de origen (su nombre), no el alumno. Incluye
 * asignaciones de bloques ya eliminados (design.md - decision D3). */
export interface StudentBlockAssignment {
  assignment_id: string;
  block_id: string;
  block_name: string;
  exercises: ExerciseProgress[];
}

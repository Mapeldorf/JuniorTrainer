/**
 * DTOs de `POST /blocks`, `GET /blocks`, `GET /blocks/{id}`, `PATCH
 * /blocks/{id}`, `DELETE /blocks/{id}`, `POST /blocks/{id}/assignments` y
 * `GET /blocks/{id}/assignments` (tarea 5.1, capacidades `exercise-blocks`
 * y `block-assignment`). Se replican a mano como interfaces TypeScript,
 * igual que `assignments-api.model.ts`/`generations-api.model.ts` -- son
 * pocos endpoints y estables (ver design.md - Decisions D6).
 */

import { ExerciseType, SavedExercise } from './generations-api.model';

export type Verdict = 'correct' | 'incomplete' | 'incorrect';

/** Body de `POST /blocks`. `exercise_ids` fija el orden: la posicion de
 * cada ejercicio en el bloque es su indice en esta lista (1 a 100
 * ejercicios). */
export interface BlockCreateRequest {
  name: string;
  exercise_ids: string[];
}

/** Body de `PATCH /blocks/{id}`. Reemplazo completo, no un diff: si se
 * manda `exercise_ids`, sustituye toda la composicion actual. Al menos
 * uno de los dos campos tiene que venir informado. */
export interface BlockUpdateRequest {
  name?: string;
  exercise_ids?: string[];
}

/** Un ejercicio de la composicion de un bloque, tal como lo devuelve el
 * detalle. */
export interface BlockExerciseItem {
  position: number;
  exercise: SavedExercise;
  /** True si el ejercicio fue eliminado del catalogo (soft-delete) desde
   * que se anadio a este bloque (tarea 1.3 de backend, design.md -
   * decision D3). */
  exercise_deleted: boolean;
}

/** Alumno asignado a un bloque, para el resumen de `BlockSummary` (tarea
 * 1.2 de backend, design.md - decision D1). */
export interface AssignedStudentSummary {
  id: string;
  name: string;
}

/** Fila de `GET /blocks`. */
export interface BlockSummary {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
  exercise_count: number;
  assigned_students: AssignedStudentSummary[];
  /** True si alguna asignacion de este bloque tiene al menos una
   * respuesta registrada (design.md - decision D2): ya no es editable,
   * pero si eliminable. */
  resolved: boolean;
}

/** Respuesta de `GET /blocks/{id}`, `POST /blocks`, `PATCH /blocks/{id}`
 * y `DELETE /blocks/{id}`. */
export interface BlockDetail {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
  deleted_at: string | null;
  exercises: BlockExerciseItem[];
  /** Mismo significado que en `BlockSummary`. */
  resolved: boolean;
}

/** Body de `POST /blocks/{id}/assignments`. */
export interface AssignBlockRequest {
  student_ids: string[];
}

export type AssignmentOutcome = 'created' | 'already_assigned';

export interface AssignmentResult {
  student_id: string;
  status: AssignmentOutcome;
}

/** Respuesta de `POST /blocks/{id}/assignments`: quien ya tenia el
 * bloque asignado se omite sin error (`already_assigned`), no falla la
 * asignacion de los demas. */
export interface AssignBlockResponse {
  results: AssignmentResult[];
}

/** Un ejercicio de la copia de una asignacion, con su progreso, tal como
 * lo devuelve `GET /blocks/{id}/assignments` para el tech lead (distinto
 * de `AssignmentExerciseItem` en assignments-api.model.ts, que es la
 * vista del propio alumno). Tipo y enunciado se leen siempre desde la
 * copia de esta asignacion, nunca desde la composicion actual del bloque
 * (tarea 3.2 de backend, design.md - decision D5). */
export interface ExerciseProgress {
  exercise_id: string;
  position: number;
  type: ExerciseType;
  statement: string;
  answered: boolean;
  verdict: Verdict | null;
  /** Texto de la respuesta y justificacion de la valoracion, solo cuando
   * `answered` es true. */
  answer_text: string | null;
  justification: string | null;
}

/** El progreso de un alumno asignado a un bloque. */
export interface StudentProgress {
  student_id: string;
  student_name: string;
  assignment_id: string;
  exercises: ExerciseProgress[];
}

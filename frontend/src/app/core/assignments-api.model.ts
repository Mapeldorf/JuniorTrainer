/**
 * DTOs de `GET /assignments`, `GET /assignments/{id}` y `POST
 * .../answer` (tarea 2.1, capacidades `student-assignments` y
 * `answer-evaluation`). Se replican a mano como interfaces TypeScript en
 * vez de generar un cliente desde OpenAPI: solo son tres endpoints y son
 * estables (ver design.md - Decisions).
 */

export type Verdict = 'correct' | 'incomplete' | 'incorrect';

/** Un fragmento de codigo de un ejercicio (espejo de `ExerciseCodeBlock`
 * en el backend), en solo lectura para el alumno. */
export interface ExerciseCodeBlock {
  file: string;
  start_line: number;
  code: string;
}

/** Una fila de `GET /assignments` (tarea 1.2 de backend): ya incluye el
 * progreso para separar pendientes de hechos. */
export interface AssignmentSummary {
  id: string;
  block_name: string;
  assigned_at: string;
  answered_count: number;
  total_count: number;
}

/** Un ejercicio de la copia de una asignacion, tal como lo devuelve `GET
 * /assignments/{id}` para un alumno (tarea 1.3 de backend): solo hasta el
 * primero sin responder inclusive, con la valoracion de los ya
 * respondidos. */
export interface AssignmentExerciseItem {
  exercise_id: string;
  position: number;
  statement: string;
  code: ExerciseCodeBlock[];
  answered: boolean;
  answer_text: string | null;
  verdict: Verdict | null;
  justification: string | null;
}

export interface AssignmentDetail {
  id: string;
  block_name: string;
  assigned_at: string;
  exercises: AssignmentExerciseItem[];
}

export interface AnswerResult {
  exercise_id: string;
  verdict: Verdict;
  justification: string | null;
  answered_at: string;
}

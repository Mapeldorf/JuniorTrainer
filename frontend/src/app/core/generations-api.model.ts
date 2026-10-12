/**
 * DTOs de `GET /generations`, `POST /generations`, `GET
 * /generations/{id}`, `POST /generations/{id}/close`, `GET /exercises`,
 * `POST /exercises/{id}/save` y `PATCH /exercises/{id}` (tarea 2.1,
 * capacidades `exercise-generation` y `exercise-catalog`). Se replican a
 * mano como interfaces TypeScript, igual que `assignments-api.model.ts`
 * -- son pocos endpoints y estables (ver design.md - Decisions).
 */

export type GenerationStatus = 'generating' | 'ready' | 'done' | 'error';
export type GenerationKind = 'knowledge' | 'debug' | 'both';
export type ExerciseType = 'knowledge' | 'debug';

/** Un fragmento de codigo de un candidato/ejercicio (espejo de
 * `ExerciseCodeBlock` en schemas/generation.py), en solo lectura -- el
 * codigo del repo nunca se muestra como editable (seccion 11). */
export interface ExerciseCodeBlock {
  file: string | null;
  code: string;
}

/** Body de `POST /generations` (tarea 6.2 de backend). Esta parte solo
 * expone `kind: 'knowledge'` y `repo_path: null` en el formulario
 * (design.md - Decisions "sin repositorio solo conocimiento"), pero el
 * tipo admite los tres valores del backend. */
export interface StartGenerationRequest {
  technologies: string[];
  repo_path: string | null;
  kind: GenerationKind;
  count: number;
}

export interface StartGenerationResponse {
  id: string;
}

/** Fila de `GET /generations` (tarea 1.2 de backend): generaciones no
 * cerradas (`status != 'done'`), para la lista de pendientes de la
 * pantalla 2. */
export interface GenerationSummary {
  id: string;
  status: GenerationStatus;
  technologies: string[];
  repo_path: string | null;
  kind: GenerationKind;
  error_message: string | null;
  created_at: string;
}

/** Un ejercicio candidato de una generacion, tal como lo devuelve `GET
 * /generations/{id}` (tarea 6.3 de backend) -- solo cuando esta
 * `ready`. */
export interface ExerciseCandidate {
  id: string;
  type: ExerciseType;
  statement: string;
  code: ExerciseCodeBlock[];
  expected_answer: string | null;
}

/** Respuesta de `GET /generations/{id}`: en curso, lista con sus
 * candidatos, o en error con el mensaje de la causa. */
export interface GenerationDetail {
  id: string;
  status: GenerationStatus;
  error_message: string | null;
  candidates: ExerciseCandidate[];
}

/** Body opcional de `POST /exercises/{id}/save` (tarea 1.4 de backend):
 * si se omite, se guarda la respuesta esperada generada. */
export interface SaveExerciseRequest {
  expected_answer?: string | null;
}

/** Un ejercicio ya guardado como definitivo (mismos campos que
 * `ExerciseCandidate`). Lo devuelven `POST /exercises/{id}/save` y
 * `PATCH /exercises/{id}`. */
export type SavedExercise = ExerciseCandidate;

/** Fila de `GET /exercises` (tarea 1.5 de backend, capacidad
 * exercise-catalog: "Listar y buscar ejercicios definitivos"): anade las
 * tecnologias y el repositorio de la generacion de cada ejercicio, sin
 * filtrar por si esa generacion ya esta `done` (design.md decision 9) --
 * es lo que pide mostrar la tabla de guardados "via su generation"
 * (seccion 10, pantalla 2). */
export interface SavedExerciseListItem extends ExerciseCandidate {
  technologies: string[];
  repo_path: string | null;
}

/** Filtros opcionales de `GET /exercises` (tarea 2.3 de backend). */
export interface ListSavedExercisesFilters {
  type?: ExerciseType;
  q?: string;
}

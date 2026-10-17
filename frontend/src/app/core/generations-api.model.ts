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

/** Body de `POST /generations` (tarea 6.2 de backend, actualizado por el
 * change `acceso-repo-github-tool`: el repositorio ya no es una ruta
 * local/URL libre, es una referencia `owner`/`repo` de GitHub). Esta
 * parte solo expone `kind: 'knowledge'` y `owner`/`repo: null` en el
 * formulario (design.md - Decisions "sin repositorio solo
 * conocimiento"), pero el tipo admite los tres valores del backend. */
export interface StartGenerationRequest {
  technologies: string[];
  owner: string | null;
  repo: string | null;
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
  repo: string | null;
  kind: GenerationKind;
  error_message: string | null;
  created_at: string;
}

/** Un ejercicio candidato de una generacion, tal como lo devuelve `GET
 * /generations/{id}` (tarea 6.3 de backend) -- solo cuando esta
 * `ready`. `name` (change `ejercicios-con-nombre`) es una etiqueta corta
 * distinta del enunciado, pensada como identificador visual en
 * listados/selectores -- nunca sustituye a `statement`, que sigue siendo
 * el texto que resuelve el alumno. */
export interface ExerciseCandidate {
  id: string;
  type: ExerciseType;
  name: string;
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

/** Body opcional de `POST /exercises/{id}/save` (tarea 1.4 de backend y
 * change `ejercicios-con-nombre`): si se omite `expected_answer` y/o
 * `name`, se guardan los generados. */
export interface SaveExerciseRequest {
  name?: string | null;
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
  repo: string | null;
  /** En cuantos bloques (activos o eliminados) esta este ejercicio
   * actualmente (tarea 2.1/5.3 de backend/frontend-tech-lead-bloques):
   * "Sin usar" / "En N bloque(s)" en el selector de la pantalla 6. */
  block_usage_count: number;
}

/** Respuesta paginada de `GET /exercises` (change
 * `paginacion-ejercicios-guardados`, capacidad exercise-catalog). `items` es
 * la pagina pedida (o todos los coincidentes si no se indica `page_size`),
 * `total` el numero de coincidencias con los filtros aplicados --para
 * calcular el numero de paginas-- y `page`/`page_size` la pagina servida y su
 * tamano (`page_size` = `total` cuando no se pagina). */
export interface SavedExercisesPage {
  items: SavedExerciseListItem[];
  total: number;
  page: number;
  page_size: number;
}

/** Filtros opcionales de `GET /exercises` (tarea 2.3 de backend, ampliados
 * con paginacion por el change `paginacion-ejercicios-guardados`). `page` es
 * 1-based y `page_size` opcional: si se omite, el backend devuelve todos los
 * coincidentes (lo que necesita la composicion de bloques). */
export interface ListSavedExercisesFilters {
  type?: ExerciseType;
  q?: string;
  page?: number;
  page_size?: number;
}

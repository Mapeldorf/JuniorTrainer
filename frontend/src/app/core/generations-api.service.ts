import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import {
  GenerationDetail,
  GenerationSummary,
  ListSavedExercisesFilters,
  SavedExercise,
  SavedExercisesPage,
  StartGenerationRequest,
  StartGenerationResponse,
  Technology,
} from './generations-api.model';

/**
 * Cliente de los endpoints de generaciones y ejercicios del tech lead
 * hacia FastAPI (tarea 2.2, capacidades `exercise-generation` y
 * `exercise-catalog`). Mismo patron que `AssignmentsApiService`, pero en
 * un servicio aparte (design.md - Decisions): capacidad distinta. El JWT
 * lo adjunta `authInterceptor`, no este servicio.
 */
@Injectable({ providedIn: 'root' })
export class GenerationsApiService {
  private readonly http = inject(HttpClient);

  listPending(): Observable<GenerationSummary[]> {
    return this.http.get<GenerationSummary[]>(`${environment.apiUrl}/generations`);
  }

  /** `GET /generations/pending/wait` (propuesta
   * `long-polling-generaciones-pendientes`): espera larga en el backend,
   * que responde en cuanto cambia alguna generacion pendiente o, si no
   * cambia nada, al cabo de un timeout acotado (~25s); en ambos casos
   * devuelve el listado de pendientes vigente. Sustituye al sondeo cada
   * 3s de `listPending()` mientras haya alguna generacion `generating`. */
  waitForPendingChange(): Observable<GenerationSummary[]> {
    return this.http.get<GenerationSummary[]>(`${environment.apiUrl}/generations/pending/wait`);
  }

  start(body: StartGenerationRequest): Observable<StartGenerationResponse> {
    return this.http.post<StartGenerationResponse>(`${environment.apiUrl}/generations`, body);
  }

  /** `GET /technologies` (change `catalogo-tecnologias`): catalogo canonico de
   * tecnologias, para poblar el selector determinista del formulario de
   * generacion. */
  getTechnologies(): Observable<Technology[]> {
    return this.http.get<Technology[]>(`${environment.apiUrl}/technologies`);
  }

  /** `POST /technologies` (change `generacion-tecnologias`): da de alta una
   * tecnologia en el catalogo. El backend la valida con el agente juez antes
   * de guardarla (403/409/422/502 se propagan al llamante). */
  createTechnology(name: string): Observable<Technology> {
    return this.http.post<Technology>(`${environment.apiUrl}/technologies`, { name });
  }

  getDetail(generationId: string): Observable<GenerationDetail> {
    return this.http.get<GenerationDetail>(`${environment.apiUrl}/generations/${generationId}`);
  }

  close(generationId: string): Observable<GenerationSummary> {
    return this.http.post<GenerationSummary>(
      `${environment.apiUrl}/generations/${generationId}/close`,
      {},
    );
  }

  /** `DELETE /generations/{id}` (change `eliminar-generaciones-por-revisar`):
   * elimina una generacion `ready` junto con sus candidatos. El backend
   * responde 204 sin cuerpo. */
  deleteGeneration(generationId: string): Observable<void> {
    return this.http.delete<void>(`${environment.apiUrl}/generations/${generationId}`);
  }

  /** `GET /exercises` (change `paginacion-ejercicios-guardados`): devuelve un
   * sobre `{ items, total, page, page_size }`. `page`/`page_size` son
   * opcionales; sin `page_size` el backend devuelve todos los coincidentes,
   * que es lo que necesita la composicion de bloques (design.md D4). */
  listSaved(filters: ListSavedExercisesFilters = {}): Observable<SavedExercisesPage> {
    let params = new HttpParams();
    if (filters.type) {
      params = params.set('type', filters.type);
    }
    if (filters.q) {
      params = params.set('q', filters.q);
    }
    if (filters.page !== undefined) {
      params = params.set('page', filters.page);
    }
    if (filters.page_size !== undefined) {
      params = params.set('page_size', filters.page_size);
    }
    return this.http.get<SavedExercisesPage>(`${environment.apiUrl}/exercises`, { params });
  }

  /** `overrides.name`/`overrides.expected_answer` (change
   * `ejercicios-con-nombre`): si vienen informados, sustituyen al nombre
   * y/o a la respuesta esperada generados; se omiten del body si no se
   * indican, para conservar los originales (design.md decision 4 de
   * `generacion-ejercicios-agentes`, extendida al nombre). */
  save(
    exerciseId: string,
    overrides: { name?: string | null; expected_answer?: string | null } = {},
  ): Observable<SavedExercise> {
    const body: { name?: string; expected_answer?: string } = {};
    if (overrides.name != null) {
      body.name = overrides.name;
    }
    if (overrides.expected_answer != null) {
      body.expected_answer = overrides.expected_answer;
    }
    return this.http.post<SavedExercise>(`${environment.apiUrl}/exercises/${exerciseId}/save`, body);
  }

  delete(exerciseId: string): Observable<SavedExercise> {
    return this.http.patch<SavedExercise>(`${environment.apiUrl}/exercises/${exerciseId}`, {
      deleted: true,
    });
  }
}

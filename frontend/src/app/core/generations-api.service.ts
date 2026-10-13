import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import {
  GenerationDetail,
  GenerationSummary,
  ListSavedExercisesFilters,
  SavedExercise,
  SavedExerciseListItem,
  StartGenerationRequest,
  StartGenerationResponse,
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

  start(body: StartGenerationRequest): Observable<StartGenerationResponse> {
    return this.http.post<StartGenerationResponse>(`${environment.apiUrl}/generations`, body);
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

  listSaved(filters: ListSavedExercisesFilters = {}): Observable<SavedExerciseListItem[]> {
    let params = new HttpParams();
    if (filters.type) {
      params = params.set('type', filters.type);
    }
    if (filters.q) {
      params = params.set('q', filters.q);
    }
    return this.http.get<SavedExerciseListItem[]>(`${environment.apiUrl}/exercises`, { params });
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

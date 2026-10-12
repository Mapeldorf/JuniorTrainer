import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import {
  AssignBlockRequest,
  AssignBlockResponse,
  BlockCreateRequest,
  BlockDetail,
  BlockSummary,
  BlockUpdateRequest,
  StudentProgress,
} from './blocks-api.model';

/**
 * Cliente de los endpoints de bloques del tech lead hacia FastAPI (tarea
 * 5.2, capacidades `exercise-blocks` y `block-assignment`). Servicio
 * aparte de `GenerationsApiService`/`AssignmentsApiService` (design.md -
 * decision D6: capacidad distinta, mismo patron). El JWT lo adjunta
 * `authInterceptor`, no este servicio.
 */
@Injectable({ providedIn: 'root' })
export class BlocksApiService {
  private readonly http = inject(HttpClient);

  list(deleted = false): Observable<BlockSummary[]> {
    const params = new HttpParams().set('deleted', String(deleted));
    return this.http.get<BlockSummary[]>(`${environment.apiUrl}/blocks`, { params });
  }

  create(body: BlockCreateRequest): Observable<BlockDetail> {
    return this.http.post<BlockDetail>(`${environment.apiUrl}/blocks`, body);
  }

  getDetail(blockId: string): Observable<BlockDetail> {
    return this.http.get<BlockDetail>(`${environment.apiUrl}/blocks/${blockId}`);
  }

  update(blockId: string, body: BlockUpdateRequest): Observable<BlockDetail> {
    return this.http.patch<BlockDetail>(`${environment.apiUrl}/blocks/${blockId}`, body);
  }

  delete(blockId: string): Observable<BlockDetail> {
    return this.http.delete<BlockDetail>(`${environment.apiUrl}/blocks/${blockId}`);
  }

  assign(blockId: string, studentIds: string[]): Observable<AssignBlockResponse> {
    const body: AssignBlockRequest = { student_ids: studentIds };
    return this.http.post<AssignBlockResponse>(
      `${environment.apiUrl}/blocks/${blockId}/assignments`,
      body,
    );
  }

  getProgress(blockId: string): Observable<StudentProgress[]> {
    return this.http.get<StudentProgress[]>(`${environment.apiUrl}/blocks/${blockId}/assignments`);
  }
}

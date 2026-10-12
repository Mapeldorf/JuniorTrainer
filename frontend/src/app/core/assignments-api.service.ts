import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import {
  AnswerResult,
  AssignmentDetail,
  AssignmentSummary,
} from './assignments-api.model';

/**
 * Cliente de los tres endpoints de asignaciones del alumno hacia FastAPI
 * (tarea 2.3, capacidades `student-assignments` y `answer-evaluation`).
 * El JWT lo adjunta `authInterceptor`, no este servicio.
 */
@Injectable({ providedIn: 'root' })
export class AssignmentsApiService {
  private readonly http = inject(HttpClient);

  listMine(): Observable<AssignmentSummary[]> {
    return this.http.get<AssignmentSummary[]>(`${environment.apiUrl}/assignments`);
  }

  getDetail(assignmentId: string): Observable<AssignmentDetail> {
    return this.http.get<AssignmentDetail>(`${environment.apiUrl}/assignments/${assignmentId}`);
  }

  submitAnswer(assignmentId: string, exerciseId: string, text: string): Observable<AnswerResult> {
    return this.http.post<AnswerResult>(
      `${environment.apiUrl}/assignments/${assignmentId}/exercises/${exerciseId}/answer`,
      { text },
    );
  }
}

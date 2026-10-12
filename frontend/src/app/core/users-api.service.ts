import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import {
  InviteStudentRequest,
  InviteStudentResponse,
  StudentBlockAssignment,
  StudentSummary,
} from './users-api.model';

/**
 * Cliente de `GET /users` (capacidad `user-auth`, tarea 8.3 de
 * frontend-tech-lead-bloques), `POST /users` y `GET /users/{id}/blocks`
 * (capacidad `block-assignment`, tarea 3.2 de frontend-tech-lead-alumnos).
 * El JWT lo adjunta `authInterceptor`.
 */
@Injectable({ providedIn: 'root' })
export class UsersApiService {
  private readonly http = inject(HttpClient);

  listStudents(): Observable<StudentSummary[]> {
    return this.http.get<StudentSummary[]>(`${environment.apiUrl}/users`);
  }

  /** Invita a un alumno nuevo. Un email duplicado devuelve 409; se deja
   * propagar el error sin envolverlo para que el componente lo distinga
   * (tasks.md - tarea 3.2). */
  invite(body: InviteStudentRequest): Observable<InviteStudentResponse> {
    return this.http.post<InviteStudentResponse>(`${environment.apiUrl}/users`, body);
  }

  getBlocks(studentId: string): Observable<StudentBlockAssignment[]> {
    return this.http.get<StudentBlockAssignment[]>(`${environment.apiUrl}/users/${studentId}/blocks`);
  }
}

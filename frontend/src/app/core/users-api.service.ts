import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { StudentSummary } from './users-api.model';

/**
 * Cliente de `GET /users` (capacidad `user-auth`, tarea 8.3 de
 * frontend-tech-lead-bloques): solo lo que necesita la pantalla 7 para
 * "Asignar a mas alumnos" -- la lista completa de alumnos, de la que se
 * excluyen los ya asignados. El JWT lo adjunta `authInterceptor`.
 */
@Injectable({ providedIn: 'root' })
export class UsersApiService {
  private readonly http = inject(HttpClient);

  listStudents(): Observable<StudentSummary[]> {
    return this.http.get<StudentSummary[]>(`${environment.apiUrl}/users`);
  }
}

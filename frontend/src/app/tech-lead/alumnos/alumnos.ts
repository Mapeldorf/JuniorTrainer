import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { StudentSummary } from '../../core/users-api.model';
import { UsersApiService } from '../../core/users-api.service';
import { TechLeadNavComponent } from '../tech-lead-nav/tech-lead-nav';

type Banner = { kind: 'success' | 'duplicate' | 'error'; message: string };

/**
 * Pantalla 5b "Alumnos" (tarea 4.1, capacidad `user-auth`: reusa
 * `POST /users` y `GET /users` ya implementados, sin cambios de backend).
 * Formulario para invitar a un alumno nuevo (nombre + email) y tabla de
 * alumnos existentes con enlace a su detalle (pantalla 5c). Un email
 * duplicado (409) marca el campo email invalido y conserva lo escrito
 * (design.md - Risks/Trade-offs); cualquier otro error muestra un banner
 * generico; el exito limpia el formulario y recarga la tabla.
 */
@Component({
  selector: 'app-alumnos',
  standalone: true,
  imports: [FormsModule, TechLeadNavComponent],
  templateUrl: './alumnos.html',
})
export class AlumnosComponent implements OnInit {
  private readonly api = inject(UsersApiService);
  private readonly router = inject(Router);

  readonly students = signal<StudentSummary[]>([]);
  readonly loading = signal(true);
  readonly name = signal('');
  readonly email = signal('');
  readonly submitting = signal(false);
  readonly banner = signal<Banner | null>(null);

  ngOnInit(): void {
    this.cargar();
  }

  private cargar(): void {
    this.loading.set(true);
    this.api.listStudents().subscribe({
      next: (students) => {
        this.students.set(students);
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
      },
    });
  }

  invitar(): void {
    const name = this.name().trim();
    const email = this.email().trim();
    if (!name || !email || this.submitting()) {
      return;
    }
    this.submitting.set(true);
    this.api.invite({ name, email }).subscribe({
      next: () => {
        this.banner.set({ kind: 'success', message: `Invitación enviada a ${email}.` });
        this.name.set('');
        this.email.set('');
        this.submitting.set(false);
        this.cargar();
      },
      error: (err: HttpErrorResponse) => {
        this.banner.set(
          err.status === 409
            ? { kind: 'duplicate', message: `Ya existe un alumno con el email ${email}.` }
            : { kind: 'error', message: 'No se ha podido invitar al alumno.' },
        );
        this.submitting.set(false);
      },
    });
  }

  verDetalle(student: StudentSummary): void {
    void this.router.navigate(['/alumnos', student.id]);
  }
}

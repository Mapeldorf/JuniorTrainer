import { Component, effect, inject, input, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Verdict } from '../../core/blocks-api.model';
import { StudentBlockAssignment, StudentSummary } from '../../core/users-api.model';
import { UsersApiService } from '../../core/users-api.service';
import { TechLeadNavComponent } from '../tech-lead-nav/tech-lead-nav';

/**
 * Pantalla 5c "Detalle de un alumno" (tareas 5.1-5.2, capacidad
 * `block-assignment`, requisito "Consultar las asignaciones de un alumno
 * a traves de sus bloques"): cabecera con nombre/email del alumno
 * (resuelto buscandolo en `UsersApiService.listStudents()`, design.md -
 * decision D del no-goal: sin endpoint dedicado para un solo alumno) y,
 * para cada bloque asignado (incluidos los ya eliminados, decision D3),
 * un desplegable con su resumen de estado y el detalle ejercicio a
 * ejercicio -- mismo nivel de detalle que `BloqueDetalleComponent`, pero
 * organizado por alumno en vez de por bloque (decision D8: vista
 * distinta, no el mismo componente).
 */
@Component({
  selector: 'app-alumno-detalle',
  standalone: true,
  imports: [RouterLink, TechLeadNavComponent],
  templateUrl: './alumno-detalle.html',
})
export class AlumnoDetalleComponent {
  readonly studentId = input.required<string>();

  private readonly usersApi = inject(UsersApiService);

  readonly student = signal<StudentSummary | null>(null);
  readonly assignments = signal<StudentBlockAssignment[]>([]);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly expandedAssignmentId = signal<string | null>(null);

  constructor() {
    effect(() => {
      const studentId = this.studentId();
      this.cargar(studentId);
    });
  }

  private cargar(studentId: string): void {
    this.loading.set(true);
    this.error.set(null);

    this.usersApi.listStudents().subscribe({
      next: (students) => {
        this.student.set(students.find((s) => s.id === studentId) ?? null);
      },
      error: () => undefined,
    });

    this.usersApi.getBlocks(studentId).subscribe({
      next: (assignments) => {
        this.assignments.set(assignments);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('No se ha podido cargar el progreso del alumno.');
        this.loading.set(false);
      },
    });
  }

  answeredCount(a: StudentBlockAssignment): number {
    return a.exercises.filter((e) => e.answered).length;
  }

  statusLabel(a: StudentBlockAssignment): string {
    const total = a.exercises.length;
    const answered = this.answeredCount(a);
    if (answered === 0) {
      return 'Sin empezar';
    }
    if (answered === total) {
      return 'Completado';
    }
    return 'En curso';
  }

  verdictCounts(a: StudentBlockAssignment): { correct: number; incomplete: number; incorrect: number } {
    let correct = 0;
    let incomplete = 0;
    let incorrect = 0;
    for (const e of a.exercises) {
      if (e.verdict === 'correct') {
        correct++;
      } else if (e.verdict === 'incomplete') {
        incomplete++;
      } else if (e.verdict === 'incorrect') {
        incorrect++;
      }
    }
    return { correct, incomplete, incorrect };
  }

  verdictSummary(a: StudentBlockAssignment): string {
    if (this.answeredCount(a) === 0) {
      return 'Sin respuestas';
    }
    const counts = this.verdictCounts(a);
    return [
      this.plural(counts.correct, 'correcta', 'correctas'),
      this.plural(counts.incomplete, 'incompleta', 'incompletas'),
      this.plural(counts.incorrect, 'incorrecta', 'incorrectas'),
    ].join(' · ');
  }

  private plural(count: number, singular: string, plural: string): string {
    return `${count} ${count === 1 ? singular : plural}`;
  }

  tipoLabel(type: 'knowledge' | 'debug'): string {
    return type === 'knowledge' ? 'Conocimiento' : 'Depuración';
  }

  verdictLabel(verdict: Verdict | null): string {
    if (verdict === 'correct') {
      return 'Correcta';
    }
    if (verdict === 'incomplete') {
      return 'Incompleta';
    }
    if (verdict === 'incorrect') {
      return 'Incorrecta';
    }
    return '';
  }

  toggleExpanded(assignmentId: string): void {
    this.expandedAssignmentId.set(
      this.expandedAssignmentId() === assignmentId ? null : assignmentId,
    );
  }

  isExpanded(assignmentId: string): boolean {
    return this.expandedAssignmentId() === assignmentId;
  }
}

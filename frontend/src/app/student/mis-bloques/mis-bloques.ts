import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { AssignmentsApiService } from '../../core/assignments-api.service';
import { AssignmentSummary } from '../../core/assignments-api.model';
import { BrandMarkComponent } from '../../core/brand-mark';
import { SupabaseService } from '../../core/supabase.service';

/**
 * Pantalla 8 "Mis bloques de ejercicios" (tarea 3.1, capacidad
 * `student-assignments`): separa las asignaciones del alumno en
 * pendientes y hechas segun su progreso, con "Empezar"/"Continuar" en
 * las pendientes y "Consultar" en las hechas (tarea 3.2).
 */
@Component({
  selector: 'app-mis-bloques',
  standalone: true,
  imports: [BrandMarkComponent],
  templateUrl: './mis-bloques.html',
})
export class MisBloquesComponent implements OnInit {
  private readonly assignmentsApi = inject(AssignmentsApiService);
  private readonly supabase = inject(SupabaseService);
  private readonly router = inject(Router);

  readonly assignments = signal<AssignmentSummary[]>([]);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);

  readonly pendientes = computed(() =>
    this.assignments().filter((a) => a.answered_count < a.total_count),
  );
  readonly hechos = computed(() =>
    this.assignments().filter((a) => a.answered_count >= a.total_count && a.total_count > 0),
  );

  ngOnInit(): void {
    this.assignmentsApi.listMine().subscribe({
      next: (assignments) => {
        this.assignments.set(assignments);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('No se han podido cargar tus bloques de ejercicios.');
        this.loading.set(false);
      },
    });
  }

  /** "Empezar" si no hay nada respondido, "Continuar" si hay alguno
   * pendiente: tarea 3.1. */
  pendienteLabel(assignment: AssignmentSummary): string {
    return assignment.answered_count === 0 ? 'Empezar' : 'Continuar';
  }

  /** La posicion a abrir es siempre el siguiente ejercicio sin responder
   * (tarea 3.2); para "Consultar" (bloque hecho) se abre desde el
   * primero. */
  abrir(assignment: AssignmentSummary): void {
    const position = assignment.answered_count < assignment.total_count
      ? assignment.answered_count + 1
      : 1;
    void this.router.navigate(['/mis-bloques', assignment.id, 'ejercicios', position]);
  }

  async signOut(): Promise<void> {
    await this.supabase.signOut();
    await this.router.navigate(['/login']);
  }
}

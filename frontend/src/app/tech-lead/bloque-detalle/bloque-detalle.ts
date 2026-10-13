import { Component, effect, inject, input, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { BlocksApiService } from '../../core/blocks-api.service';
import { ConfirmDialogService } from '../../core/confirm-dialog.service';
import { BlockDetail, StudentProgress } from '../../core/blocks-api.model';
import { UsersApiService } from '../../core/users-api.service';
import { StudentSummary } from '../../core/users-api.model';
import { TechLeadNavComponent } from '../tech-lead-nav/tech-lead-nav';

/**
 * Pantalla 7 "Detalle del bloque y asignacion" / 7b "Bloque eliminado"
 * (tareas 8.1-8.4, capacidades `exercise-blocks` y `block-assignment`).
 * Un solo componente para ambas (design.md - decision D8): si el bloque
 * esta eliminado (`deleted_at` informado), se ocultan "Editar"/
 * "Eliminar"/"Asignar a mas alumnos" y la vista queda en solo lectura.
 * "Editar bloque" se deshabilita si el bloque esta `resolved`.
 */
@Component({
  selector: 'app-bloque-detalle',
  standalone: true,
  imports: [FormsModule, TechLeadNavComponent],
  templateUrl: './bloque-detalle.html',
})
export class BloqueDetalleComponent {
  readonly blockId = input.required<string>();

  private readonly blocksApi = inject(BlocksApiService);
  private readonly usersApi = inject(UsersApiService);
  private readonly router = inject(Router);
  private readonly confirmDialog = inject(ConfirmDialogService);

  readonly block = signal<BlockDetail | null>(null);
  readonly progress = signal<StudentProgress[]>([]);
  readonly allStudents = signal<StudentSummary[]>([]);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);

  readonly studentSearch = signal('');
  readonly expandedAssignmentId = signal<string | null>(null);
  readonly selectedToAssign = signal<string[]>([]);

  constructor() {
    effect(() => {
      const blockId = this.blockId();
      this.cargar(blockId);
    });
  }

  private cargar(blockId: string): void {
    this.loading.set(true);
    this.error.set(null);
    this.blocksApi.getDetail(blockId).subscribe({
      next: (detail) => {
        this.block.set(detail);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('No se ha podido cargar el bloque.');
        this.loading.set(false);
      },
    });
    this.blocksApi.getProgress(blockId).subscribe({
      next: (progress) => this.progress.set(progress),
      error: () => this.error.set('No se ha podido cargar el progreso de los alumnos.'),
    });
    this.usersApi.listStudents().subscribe({
      next: (students) => this.allStudents.set(students),
      error: () => undefined,
    });
  }

  get isDeleted(): boolean {
    return this.block()?.deleted_at != null;
  }

  get filteredProgress(): StudentProgress[] {
    const q = this.studentSearch().trim().toLowerCase();
    if (!q) {
      return this.progress();
    }
    return this.progress().filter((p) => p.student_name.toLowerCase().includes(q));
  }

  statusLabel(p: StudentProgress): string {
    const total = p.exercises.length;
    const answered = p.exercises.filter((e) => e.answered).length;
    if (answered === 0) {
      return 'Sin empezar';
    }
    if (answered === total) {
      return 'Completado';
    }
    return 'En curso';
  }

  answeredCount(p: StudentProgress): number {
    return p.exercises.filter((e) => e.answered).length;
  }

  verdictCounts(p: StudentProgress): { correct: number; incomplete: number; incorrect: number } {
    let correct = 0;
    let incomplete = 0;
    let incorrect = 0;
    for (const e of p.exercises) {
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

  toggleExpanded(assignmentId: string): void {
    this.expandedAssignmentId.set(
      this.expandedAssignmentId() === assignmentId ? null : assignmentId,
    );
  }

  isExpanded(assignmentId: string): boolean {
    return this.expandedAssignmentId() === assignmentId;
  }

  get unassignedStudents(): StudentSummary[] {
    const assignedIds = new Set(this.progress().map((p) => p.student_id));
    return this.allStudents().filter((s) => !assignedIds.has(s.id));
  }

  isSelectedToAssign(studentId: string): boolean {
    return this.selectedToAssign().includes(studentId);
  }

  toggleToAssign(studentId: string): void {
    const current = this.selectedToAssign();
    this.selectedToAssign.set(
      current.includes(studentId)
        ? current.filter((id) => id !== studentId)
        : [...current, studentId],
    );
  }

  asignar(): void {
    const ids = this.selectedToAssign();
    if (ids.length === 0) {
      return;
    }
    this.blocksApi.assign(this.blockId(), ids).subscribe({
      next: () => {
        this.selectedToAssign.set([]);
        this.cargar(this.blockId());
      },
      error: () => this.error.set('No se ha podido asignar el bloque.'),
    });
  }

  editar(): void {
    void this.router.navigate(['/bloques', this.blockId(), 'editar']);
  }

  /** change `dialogo-confirmacion-tailwind`: dialogo propio en vez de
   * `confirm()` nativo, por eso async. */
  async eliminar(): Promise<void> {
    if (!(await this.confirmarEliminar())) {
      return;
    }
    this.blocksApi.delete(this.blockId()).subscribe({
      next: (detail) => this.block.set(detail),
      error: () => this.error.set('No se ha podido eliminar el bloque.'),
    });
  }

  /** Envuelto en un metodo propio para poder sustituirlo en los tests
   * (mismo patron que `EjerciciosComponent.confirmarEliminar`). */
  confirmarEliminar(): Promise<boolean> {
    return this.confirmDialog.confirm({
      title: 'Eliminar bloque',
      message: `¿Eliminar el bloque "${this.block()?.name}"?`,
      confirmLabel: 'Eliminar',
      cancelLabel: 'Cancelar',
      destructive: true,
    });
  }
}

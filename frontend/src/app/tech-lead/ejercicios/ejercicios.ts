import { Component, OnDestroy, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ConfirmDialogService } from '../../core/confirm-dialog.service';
import { GenerationsApiService } from '../../core/generations-api.service';
import {
  ExerciseType,
  GenerationStatus,
  GenerationSummary,
  SavedExerciseListItem,
} from '../../core/generations-api.model';
import { TechLeadNavComponent } from '../tech-lead-nav/tech-lead-nav';

const POLL_INTERVAL_MS = 3000;

/**
 * Pantalla 2 "Ejercicios guardados" (tareas 4.1-4.3, capacidades
 * `exercise-generation` y `exercise-catalog`): generaciones pendientes
 * (Generando/Por revisar/Error) y tabla de ejercicios guardados con
 * tipo, tecnologias y repositorio (via su generation), filtrables por
 * tipo y busqueda de texto.
 */
@Component({
  selector: 'app-ejercicios',
  standalone: true,
  imports: [FormsModule, TechLeadNavComponent],
  templateUrl: './ejercicios.html',
})
export class EjerciciosComponent implements OnInit, OnDestroy {
  private readonly api = inject(GenerationsApiService);
  private readonly router = inject(Router);
  private readonly confirmDialog = inject(ConfirmDialogService);

  readonly pending = signal<GenerationSummary[]>([]);
  readonly saved = signal<SavedExerciseListItem[]>([]);
  readonly loadingPending = signal(true);
  readonly loadingSaved = signal(true);
  readonly error = signal<string | null>(null);

  readonly filterType = signal<ExerciseType | ''>('');
  readonly searchText = signal('');

  private pollHandle: ReturnType<typeof setInterval> | null = null;

  ngOnInit(): void {
    this.loadPending();
    this.loadSaved();
  }

  ngOnDestroy(): void {
    this.stopPolling();
  }

  /** Tarea 4.2: polling cada 3s de `listPending()` mientras haya alguna
   * generacion `generating`, deteniendolo en cuanto ninguna lo este
   * (design.md decision 1). */
  private loadPending(): void {
    this.api.listPending().subscribe({
      next: (generations) => {
        this.pending.set(generations);
        this.loadingPending.set(false);
        this.syncPolling(generations);
      },
      error: () => {
        this.error.set('No se han podido cargar las generaciones pendientes.');
        this.loadingPending.set(false);
      },
    });
  }

  private syncPolling(generations: GenerationSummary[]): void {
    const hayGenerando = generations.some((g) => g.status === 'generating');
    if (hayGenerando && this.pollHandle === null) {
      this.pollHandle = setInterval(() => this.loadPending(), POLL_INTERVAL_MS);
    } else if (!hayGenerando) {
      this.stopPolling();
    }
  }

  private stopPolling(): void {
    if (this.pollHandle !== null) {
      clearInterval(this.pollHandle);
      this.pollHandle = null;
    }
  }

  loadSaved(): void {
    this.loadingSaved.set(true);
    this.api
      .listSaved({
        type: this.filterType() || undefined,
        q: this.searchText() || undefined,
      })
      .subscribe({
        next: (items) => {
          this.saved.set(items);
          this.loadingSaved.set(false);
        },
        error: () => {
          this.error.set('No se han podido cargar los ejercicios guardados.');
          this.loadingSaved.set(false);
        },
      });
  }

  onFilterTypeChange(value: ExerciseType | ''): void {
    this.filterType.set(value);
    this.loadSaved();
  }

  onSearchTextChange(value: string): void {
    this.searchText.set(value);
    this.loadSaved();
  }

  statusLabel(status: GenerationStatus): string {
    switch (status) {
      case 'generating':
        return 'Generando';
      case 'ready':
        return 'Por revisar';
      case 'error':
        return 'Error';
      default:
        return status;
    }
  }

  generar(): void {
    void this.router.navigate(['/ejercicios/generar']);
  }

  revisar(generation: GenerationSummary): void {
    void this.router.navigate(['/ejercicios', generation.id, 'revisar']);
  }

  /** Tarea 4.3: boton Eliminar en cada ejercicio guardado, con
   * confirmacion previa (change `dialogo-confirmacion-tailwind`: dialogo
   * propio en vez de `confirm()` nativo, por eso async). */
  async eliminar(exercise: SavedExerciseListItem): Promise<void> {
    if (!(await this.confirmarEliminar(exercise))) {
      return;
    }
    this.api.delete(exercise.id).subscribe({
      next: () => this.loadSaved(),
      error: () => this.error.set('No se ha podido eliminar el ejercicio.'),
    });
  }

  /** Envuelto en un metodo propio para poder sustituirlo en los tests
   * sin depender del dialogo real. */
  confirmarEliminar(exercise: SavedExerciseListItem): Promise<boolean> {
    return this.confirmDialog.confirm({
      title: 'Eliminar ejercicio',
      message: `¿Eliminar el ejercicio "${exercise.name}"?`,
      confirmLabel: 'Eliminar',
      cancelLabel: 'Cancelar',
      destructive: true,
    });
  }
}

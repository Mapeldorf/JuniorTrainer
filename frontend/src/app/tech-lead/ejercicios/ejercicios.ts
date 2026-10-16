import { Component, OnDestroy, OnInit, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ConfirmDialogService } from '../../core/confirm-dialog.service';
import { GenerationTrackerService } from '../../core/generation-tracker.service';
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
  private readonly tracker = inject(GenerationTrackerService);

  readonly pending = signal<GenerationSummary[]>([]);
  readonly saved = signal<SavedExerciseListItem[]>([]);
  readonly loadingPending = signal(true);
  readonly loadingSaved = signal(true);
  readonly error = signal<string | null>(null);

  /** Tarea 4.2 (`ocultar-generaciones-error`): recuento de generaciones
   * lanzadas desde esta sesion que terminaron en `error`. Se mantiene
   * separado de `error` (fallos de carga de datos) para no mezclar el
   * aviso de generacion fallida con errores de la propia pantalla. */
  readonly generationFailures = signal(0);

  /** Mensaje agregado del aviso de fallos, en singular o plural; `null`
   * cuando no hay ningun fallo que anunciar. */
  readonly generationFailureNotice = computed(() => {
    const count = this.generationFailures();
    if (count <= 0) {
      return null;
    }
    return count === 1
      ? '1 generación ha fallado y no aparece en la lista porque no llegó a generar ejercicios.'
      : `${count} generaciones han fallado y no aparecen en la lista porque no llegaron a generar ejercicios.`;
  });

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
   * (design.md decision 1). Se amplia (`ocultar-generaciones-error`,
   * tarea 4.1) para consultar tambien las generaciones rastreadas y para
   * seguir sondeando mientras quede alguna rastreada por resolver. */
  private loadPending(): void {
    this.api.listPending().subscribe({
      next: (generations) => {
        // El backend ya excluye las `error`; se filtran tambien aqui como
        // red de seguridad para que la lista nunca muestre una generacion
        // fallida (requisito "Aviso de generaciones fallidas en la
        // interfaz": el sistema SHALL NOT mostrar esa generacion).
        this.pending.set(generations.filter((g) => g.status !== 'error'));
        this.loadingPending.set(false);
        this.checkTrackedGenerations();
        this.updatePolling();
      },
      error: () => {
        this.error.set('No se han podido cargar las generaciones pendientes.');
        this.loadingPending.set(false);
      },
    });
  }

  /** Arranca o detiene el polling segun haya generaciones en curso o ids
   * rastreados sin resolver. */
  private updatePolling(): void {
    const hayGenerando = this.pending().some((g) => g.status === 'generating');
    const hayRastreadas = this.tracker.list().length > 0;
    if ((hayGenerando || hayRastreadas) && this.pollHandle === null) {
      this.pollHandle = setInterval(() => this.loadPending(), POLL_INTERVAL_MS);
    } else if (!hayGenerando && !hayRastreadas) {
      this.stopPolling();
    }
  }

  /** Consulta `GET /generations/{id}` de cada generacion rastreada: si
   * termino en `error`, suma un fallo al aviso y deja de rastrearla; si ya
   * esta lista (o cerrada), simplemente deja de rastrearla (aparecera en
   * el listado). Un id que ya no existe o falla la consulta tambien se
   * descarta para no reintentar indefinidamente. */
  private checkTrackedGenerations(): void {
    const ids = this.tracker.list();
    if (ids.length === 0) {
      return;
    }
    let pendingChecks = ids.length;
    const onCheckDone = (): void => {
      pendingChecks -= 1;
      if (pendingChecks === 0) {
        this.updatePolling();
      }
    };

    for (const id of ids) {
      this.api.getDetail(id).subscribe({
        next: (detail) => {
          if (this.tracker.list().includes(id)) {
            if (detail.status === 'error') {
              this.tracker.remove(id);
              this.generationFailures.update((count) => count + 1);
            } else if (detail.status !== 'generating') {
              this.tracker.remove(id);
            }
          }
          onCheckDone();
        },
        error: () => {
          this.tracker.remove(id);
          onCheckDone();
        },
      });
    }
  }

  /** Tarea 4.3: descarta el aviso agregado de generaciones fallidas. */
  dismissGenerationFailures(): void {
    this.generationFailures.set(0);
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

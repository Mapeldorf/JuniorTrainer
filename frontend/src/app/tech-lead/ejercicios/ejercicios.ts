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
import { ExerciseDetailComponent } from '../../core/exercise-detail';
import { PaginationComponent } from '../../core/pagination';
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
  imports: [FormsModule, PaginationComponent, TechLeadNavComponent, ExerciseDetailComponent],
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
  /** Primera carga de guardados: aun no hay tabla que mostrar. */
  readonly loadingSaved = signal(true);
  /** Recarga de guardados (cambio de pagina o de filtro) con la tabla ya
   * montada: se atenua en vez de sustituirse, para no colapsar la altura de
   * la pagina y que el scroll no salte hacia arriba. */
  readonly refreshingSaved = signal(false);
  readonly error = signal<string | null>(null);

  /** Paginacion de la tabla de guardados (change
   * `paginacion-ejercicios-guardados`): 10 por pagina, con la pagina actual
   * y el total de coincidencias que devuelve `GET /exercises`. */
  readonly pageSize = 10;
  readonly page = signal(1);
  readonly total = signal(0);
  readonly totalPages = computed(() => Math.max(1, Math.ceil(this.total() / this.pageSize)));

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

  /** Ejercicio cuyo detalle se esta mostrando en el panel (change
   * `detalle-ejercicio-guardado`); `null` cuando el panel esta cerrado. */
  readonly selected = signal<SavedExerciseListItem | null>(null);

  private pollHandle: ReturnType<typeof setInterval> | null = null;

  /** Si ya se ha cargado el listado alguna vez; distingue la primera carga
   * (placeholder "Cargando…") de las recargas (tabla atenuada). */
  private hasLoadedSaved = false;

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
    // La primera carga muestra el placeholder; las recargas mantienen la
    // tabla montada (atenuada) para no colapsar la altura de la pagina y
    // evitar que el scroll salte hacia arriba al cambiar de pagina.
    const firstLoad = !this.hasLoadedSaved;
    this.hasLoadedSaved = true;
    if (firstLoad) {
      this.loadingSaved.set(true);
    } else {
      this.refreshingSaved.set(true);
    }
    this.api
      .listSaved({
        type: this.filterType() || undefined,
        q: this.searchText() || undefined,
        page: this.page(),
        page_size: this.pageSize,
      })
      .subscribe({
        next: (result) => {
          this.saved.set(result.items);
          this.total.set(result.total);
          this.loadingSaved.set(false);
          this.refreshingSaved.set(false);
        },
        error: () => {
          this.error.set('No se han podido cargar los ejercicios guardados.');
          this.loadingSaved.set(false);
          this.refreshingSaved.set(false);
        },
      });
  }

  onFilterTypeChange(value: ExerciseType | ''): void {
    this.filterType.set(value);
    this.page.set(1);
    this.loadSaved();
  }

  onSearchTextChange(value: string): void {
    this.searchText.set(value);
    this.page.set(1);
    this.loadSaved();
  }

  /** Cambia de pagina y recarga el listado (change
   * `paginacion-ejercicios-guardados`). */
  onPageChange(target: number): void {
    if (target < 1 || target > this.totalPages() || target === this.page()) {
      return;
    }
    this.page.set(target);
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

  /** Tarea 4.1 del change `eliminar-generaciones-por-revisar`: boton
   * Eliminar en cada generacion por revisar, con confirmacion previa
   * (dialogo propio via `ConfirmDialogService`, mismo patron que
   * `eliminar()` de guardados). El backend borra la generacion y sus
   * candidatos; despues se recarga el listado de pendientes. */
  async eliminarGeneracion(generation: GenerationSummary): Promise<void> {
    if (!(await this.confirmarEliminarGeneracion(generation))) {
      return;
    }
    this.api.deleteGeneration(generation.id).subscribe({
      next: () => this.loadPending(),
      error: () => this.error.set('No se ha podido eliminar la generación.'),
    });
  }

  /** Envuelto en un metodo propio (mismo patron que `confirmarEliminar()`)
   * para poder sustituirlo en los tests sin depender del dialogo real. */
  confirmarEliminarGeneracion(generation: GenerationSummary): Promise<boolean> {
    const technologies = generation.technologies.join(', ');
    return this.confirmDialog.confirm({
      title: 'Eliminar generación',
      message: `Se van a eliminar los ejercicios de la generación de ${technologies}. Esta acción no se puede deshacer.`,
      confirmLabel: 'Eliminar',
      cancelLabel: 'Cancelar',
      destructive: true,
    });
  }

  /** Abre el panel de detalle de un ejercicio guardado (change
   * `detalle-ejercicio-guardado`). Todo el contenido sale del item ya
   * cargado en el listado, sin consultas adicionales. */
  ver(exercise: SavedExerciseListItem): void {
    this.selected.set(exercise);
  }

  /** Cierra el panel de detalle. */
  cerrarDetalle(): void {
    this.selected.set(null);
  }

  /** Tarea 4.3: boton Eliminar en cada ejercicio guardado, con
   * confirmacion previa (change `dialogo-confirmacion-tailwind`: dialogo
   * propio en vez de `confirm()` nativo, por eso async). */
  async eliminar(exercise: SavedExerciseListItem): Promise<void> {
    if (!(await this.confirmarEliminar(exercise))) {
      return;
    }
    this.api.delete(exercise.id).subscribe({
      next: () => {
        // Si era el unico de esta pagina y no es la primera, retrocede para
        // no dejar al tech lead en una pagina vacia (change
        // `paginacion-ejercicios-guardados`, escenario "Eliminar el ultimo
        // ejercicio de una pagina").
        if (this.saved().length === 1 && this.page() > 1) {
          this.page.update((current) => current - 1);
        }
        this.loadSaved();
      },
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

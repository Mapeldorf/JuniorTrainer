import { Component, OnDestroy, OnInit, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { Subscription } from 'rxjs';
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

  /** Suscripcion de la espera larga en curso (`GET
   * /generations/pending/wait`, propuesta
   * `long-polling-generaciones-pendientes`); `null` cuando no hay ninguna
   * encadenada en ese momento. */
  private pendingWaitSubscription: Subscription | null = null;

  /** Si ya se ha cargado el listado alguna vez; distingue la primera carga
   * (placeholder "Cargando…") de las recargas (tabla atenuada). */
  private hasLoadedSaved = false;

  ngOnInit(): void {
    this.loadPending();
    this.loadSaved();
  }

  ngOnDestroy(): void {
    this.stopWaitLoop();
  }

  /** Primera carga (o recarga manual, p. ej. tras eliminar una
   * generacion) del listado de pendientes via `GET /generations`: responde
   * de inmediato con el estado actual, sin esperar nada. Si queda alguna
   * generacion `generating`, arranca a continuacion la espera larga
   * encadenada (`ensureWaitLoopRunning`) que sustituye al antiguo sondeo
   * cada 3s. */
  private loadPending(): void {
    this.api.listPending().subscribe({
      next: (generations) => {
        this.applyPendingResult(generations);
        this.loadingPending.set(false);
      },
      error: () => {
        this.error.set('No se han podido cargar las generaciones pendientes.');
        this.loadingPending.set(false);
      },
    });
  }

  /** Comun a `loadPending()` y a cada respuesta de la espera larga:
   * filtra las `error` (red de seguridad, requisito "Aviso de
   * generaciones fallidas en la interfaz": el sistema SHALL NOT mostrar
   * esa generacion aunque el backend ya las excluye), actualiza el
   * listado visible, resuelve las generaciones rastreadas que hayan
   * desaparecido, y decide si hace falta seguir esperando cambios. */
  private applyPendingResult(generations: GenerationSummary[]): void {
    const visible = generations.filter((g) => g.status !== 'error');
    this.pending.set(visible);
    this.checkTrackedGenerations(visible);
    this.updateWaitLoop(visible);
  }

  /** Tarea 4.1 (propuesta `long-polling-generaciones-pendientes`): arranca
   * o detiene la espera larga encadenada segun haya generaciones en curso
   * o ids rastreados sin resolver (misma condicion que el antiguo
   * `updatePolling()`). */
  private updateWaitLoop(visible: GenerationSummary[]): void {
    const hayGenerando = visible.some((g) => g.status === 'generating');
    const hayRastreadas = this.tracker.list().length > 0;
    if (hayGenerando || hayRastreadas) {
      this.ensureWaitLoopRunning();
    } else {
      this.stopWaitLoop();
    }
  }

  /** Si ya hay una espera larga en curso no hace nada (evita duplicar la
   * peticion); si no, encadena la siguiente llamada a
   * `waitForPendingChange()`. */
  private ensureWaitLoopRunning(): void {
    if (this.pendingWaitSubscription !== null) {
      return;
    }
    this.pendingWaitSubscription = this.api.waitForPendingChange().subscribe({
      next: (generations) => {
        this.pendingWaitSubscription = null;
        this.applyPendingResult(generations);
      },
      error: () => {
        // Tarea 4.3: un fallo puntual de una espera larga (p. ej. un 429)
        // no debe dejar la pantalla en un estado roto -- se avisa igual
        // que hoy, pero se reintenta con el ultimo listado conocido en vez
        // de detener el bucle.
        this.pendingWaitSubscription = null;
        this.error.set('No se han podido cargar las generaciones pendientes.');
        this.updateWaitLoop(this.pending());
      },
    });
  }

  /** Resuelve las generaciones rastreadas sin tener que consultar
   * `GET /generations/{id}` de todas ellas en cada ciclo (tarea 4.2):
   * mientras una rastreada sigue visible y `generating`, no hace falta
   * nada; si sigue visible pero ya no `generating` (`ready`), su estado
   * ya se sabe por el propio listado y se deja de rastrear sin ninguna
   * consulta -- SI NO se retirara aqui, se quedaria rastreada para
   * siempre (nunca vuelve a desaparecer del listado por si misma) y
   * `updateWaitLoop` no dejaria nunca de encadenar la espera larga. Solo
   * las que YA NO aparecen (ni `generating` ni `ready`) necesitan la
   * consulta puntual, para distinguir `error` (suma al aviso agregado) de
   * otra causa de desaparicion. */
  private checkTrackedGenerations(visible: GenerationSummary[]): void {
    const visibleById = new Map(visible.map((g) => [g.id, g]));
    const idsToQuery: string[] = [];

    for (const id of this.tracker.list()) {
      const match = visibleById.get(id);
      if (match === undefined) {
        idsToQuery.push(id);
      } else if (match.status !== 'generating') {
        this.tracker.remove(id);
      }
    }

    if (idsToQuery.length === 0) {
      return;
    }

    // `updateWaitLoop(visible)` ya se ha llamado una vez de forma eager en
    // `applyPendingResult`, con el estado del tracker de antes de resolver
    // estas consultas; se vuelve a llamar aqui cuando todas terminan, para
    // que un id que se resuelve en esta misma ronda (y que era el ultimo
    // pendiente) detenga el bucle sin esperar a otra ronda de mas.
    let pendingChecks = idsToQuery.length;
    const onCheckDone = (): void => {
      pendingChecks -= 1;
      if (pendingChecks === 0) {
        this.updateWaitLoop(visible);
      }
    };

    for (const id of idsToQuery) {
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

  private stopWaitLoop(): void {
    this.pendingWaitSubscription?.unsubscribe();
    this.pendingWaitSubscription = null;
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

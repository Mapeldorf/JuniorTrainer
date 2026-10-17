import { Component, effect, inject, input, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { BlocksApiService } from '../../core/blocks-api.service';
import { GenerationsApiService } from '../../core/generations-api.service';
import { ExerciseType, SavedExerciseListItem } from '../../core/generations-api.model';
import { TechLeadNavComponent } from '../tech-lead-nav/tech-lead-nav';

const MIN_EXERCISES = 1;
const MAX_EXERCISES = 100;

/** Fila del selector de ejercicios: une el catalogo (`GET /exercises`,
 * filtrable) con los ejercicios de la composicion actual del bloque que
 * ya fueron eliminados del catalogo (`exercise_deleted`, que por eso no
 * aparecen en el catalogo y se pinchan aparte). */
interface ExerciseRow {
  id: string;
  type: ExerciseType;
  name: string;
  statement: string;
  technologies: string[] | null;
  repoPath: string | null;
  blockUsageCount: number | null;
  exerciseDeleted: boolean;
}

/**
 * Pantalla 6 "Nuevo/editar bloque de ejercicios" (tareas 7.1-7.3,
 * capacidad exercise-blocks). Un solo componente para crear y editar
 * (design.md - decision D7): sin `blockId` (ruta `/bloques/nuevo`),
 * formulario vacio con "Crear bloque"; con `blockId` (ruta
 * `/bloques/:blockId/editar`), precarga el bloque con "Guardar
 * cambios". `exercise_ids` se manda siempre en el orden de seleccion,
 * que es tambien la posicion en el bloque.
 */
@Component({
  selector: 'app-bloque-editar',
  standalone: true,
  imports: [FormsModule, TechLeadNavComponent],
  templateUrl: './bloque-editar.html',
})
export class BloqueEditarComponent {
  readonly blockId = input<string | undefined>();

  private readonly blocksApi = inject(BlocksApiService);
  private readonly exercisesApi = inject(GenerationsApiService);
  private readonly router = inject(Router);

  readonly loading = signal(true);
  readonly saving = signal(false);
  readonly error = signal<string | null>(null);

  readonly name = signal('');
  readonly filterType = signal<ExerciseType | ''>('');
  readonly searchText = signal('');

  readonly catalogRows = signal<ExerciseRow[]>([]);
  readonly deletedRows = signal<ExerciseRow[]>([]);
  readonly selectedIds = signal<string[]>([]);

  /** Todo lo que se ha visto hasta ahora (catalogo + eliminados),
   * acumulado para que el panel de conteos siga siendo correcto aunque
   * un filtro oculte temporalmente una fila ya marcada. */
  private readonly knownRows = new Map<string, ExerciseRow>();

  constructor() {
    effect(() => {
      const blockId = this.blockId();
      if (blockId) {
        this.cargarBloque(blockId);
      } else {
        this.loading.set(false);
      }
    });
    this.cargarCatalogo();
  }

  get isEditing(): boolean {
    return !!this.blockId();
  }

  private cargarBloque(blockId: string): void {
    this.loading.set(true);
    this.blocksApi.getDetail(blockId).subscribe({
      next: (detail) => {
        this.name.set(detail.name);
        const ids: string[] = [];
        const deleted: ExerciseRow[] = [];
        for (const item of detail.exercises) {
          ids.push(item.exercise.id);
          const row: ExerciseRow = {
            id: item.exercise.id,
            type: item.exercise.type,
            name: item.exercise.name,
            statement: item.exercise.statement,
            technologies: null,
            repoPath: null,
            blockUsageCount: null,
            exerciseDeleted: item.exercise_deleted,
          };
          this.knownRows.set(row.id, row);
          if (item.exercise_deleted) {
            deleted.push(row);
          }
        }
        this.selectedIds.set(ids);
        this.deletedRows.set(deleted);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('No se ha podido cargar el bloque.');
        this.loading.set(false);
      },
    });
  }

  private cargarCatalogo(): void {
    // Sin paginacion: el backend devuelve todos los coincidentes
    // (`page.items`), que es el catalogo completo que necesita el selector
    // (change `paginacion-ejercicios-guardados`, design.md D4).
    this.exercisesApi
      .listSaved({ type: this.filterType() || undefined, q: this.searchText() || undefined })
      .subscribe({
        next: (page) => {
          const rows = page.items.map((item) => this.toRow(item));
          for (const row of rows) {
            this.knownRows.set(row.id, row);
          }
          this.catalogRows.set(rows);
        },
        error: () => {
          this.error.set('No se han podido cargar los ejercicios guardados.');
        },
      });
  }

  private toRow(item: SavedExerciseListItem): ExerciseRow {
    return {
      id: item.id,
      type: item.type,
      name: item.name,
      statement: item.statement,
      technologies: item.technologies,
      repoPath: item.repo,
      blockUsageCount: item.block_usage_count,
      exerciseDeleted: false,
    };
  }

  onFilterTypeChange(value: ExerciseType | ''): void {
    this.filterType.set(value);
    this.cargarCatalogo();
  }

  onSearchTextChange(value: string): void {
    this.searchText.set(value);
    this.cargarCatalogo();
  }

  isChecked(id: string): boolean {
    return this.selectedIds().includes(id);
  }

  toggle(id: string): void {
    const current = this.selectedIds();
    if (current.includes(id)) {
      this.selectedIds.set(current.filter((x) => x !== id));
    } else {
      this.selectedIds.set([...current, id]);
    }
  }

  usageLabel(row: ExerciseRow): string {
    if (row.blockUsageCount == null) {
      return '';
    }
    return row.blockUsageCount === 0 ? 'Sin usar' : `En ${row.blockUsageCount} bloque(s)`;
  }

  get counts(): { knowledge: number; debug: number; total: number } {
    let knowledge = 0;
    let debug = 0;
    for (const id of this.selectedIds()) {
      const row = this.knownRows.get(id);
      if (row?.type === 'knowledge') {
        knowledge++;
      } else if (row?.type === 'debug') {
        debug++;
      }
    }
    return { knowledge, debug, total: this.selectedIds().length };
  }

  get hasDeletedSelected(): boolean {
    return this.selectedIds().some((id) => this.knownRows.get(id)?.exerciseDeleted);
  }

  get canSave(): boolean {
    const count = this.selectedIds().length;
    return (
      this.name().trim().length > 0 &&
      count >= MIN_EXERCISES &&
      count <= MAX_EXERCISES &&
      !this.hasDeletedSelected
    );
  }

  guardar(): void {
    if (!this.canSave || this.saving()) {
      return;
    }
    this.saving.set(true);
    this.error.set(null);
    const body = { name: this.name().trim(), exercise_ids: this.selectedIds() };
    const blockId = this.blockId();
    const request = blockId ? this.blocksApi.update(blockId, body) : this.blocksApi.create(body);
    request.subscribe({
      next: (detail) => void this.router.navigate(['/bloques', detail.id]),
      error: () => {
        this.error.set('No se ha podido guardar el bloque.');
        this.saving.set(false);
      },
    });
  }

  cancelar(): void {
    const blockId = this.blockId();
    void this.router.navigate(blockId ? ['/bloques', blockId] : ['/bloques']);
  }
}

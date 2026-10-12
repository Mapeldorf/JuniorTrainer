import { Component, OnInit, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { BlocksApiService } from '../../core/blocks-api.service';
import { BlockSummary } from '../../core/blocks-api.model';
import { TechLeadNavComponent } from '../tech-lead-nav/tech-lead-nav';

/**
 * Pantalla 5 "Bloques de ejercicios" (tarea 6.2, capacidad
 * exercise-blocks: "Listar y ver el detalle de un bloque"): tabla de
 * bloques activos (nombre, numero de ejercicios, alumnos asignados,
 * "Resuelto · no editable" si procede) y, en una seccion colapsable
 * aparte, los bloques eliminados en solo lectura con su fecha de
 * eliminacion. "Ver detalle" y "Ver resultados" llevan al mismo
 * componente de detalle (pantalla 7/7b, design.md - decision D8).
 */
@Component({
  selector: 'app-bloques',
  standalone: true,
  imports: [TechLeadNavComponent],
  templateUrl: './bloques.html',
})
export class BloquesComponent implements OnInit {
  private readonly api = inject(BlocksApiService);
  private readonly router = inject(Router);

  readonly activos = signal<BlockSummary[]>([]);
  readonly eliminados = signal<BlockSummary[]>([]);
  readonly loadingActivos = signal(true);
  readonly loadingEliminados = signal(true);
  readonly mostrarEliminados = signal(false);
  readonly error = signal<string | null>(null);

  ngOnInit(): void {
    this.loadActivos();
    this.loadEliminados();
  }

  private loadActivos(): void {
    this.loadingActivos.set(true);
    this.api.list(false).subscribe({
      next: (blocks) => {
        this.activos.set(blocks);
        this.loadingActivos.set(false);
      },
      error: () => {
        this.error.set('No se han podido cargar los bloques.');
        this.loadingActivos.set(false);
      },
    });
  }

  private loadEliminados(): void {
    this.loadingEliminados.set(true);
    this.api.list(true).subscribe({
      next: (blocks) => {
        this.eliminados.set(blocks);
        this.loadingEliminados.set(false);
      },
      error: () => {
        this.loadingEliminados.set(false);
      },
    });
  }

  toggleEliminados(): void {
    this.mostrarEliminados.set(!this.mostrarEliminados());
  }

  nuevoBloque(): void {
    void this.router.navigate(['/bloques/nuevo']);
  }

  verDetalle(block: BlockSummary): void {
    void this.router.navigate(['/bloques', block.id]);
  }

  nombresAlumnos(block: BlockSummary): string {
    if (block.assigned_students.length === 0) {
      return 'Sin asignar';
    }
    return block.assigned_students.map((s) => s.name).join(', ');
  }

  formatFecha(iso: string): string {
    return new Date(iso).toLocaleDateString('es-ES');
  }
}

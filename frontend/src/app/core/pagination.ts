import { Component, computed, input, output } from '@angular/core';

/**
 * Control de paginacion reutilizable (change `paginacion-ejercicios-guardados`,
 * capacidad exercise-catalog), con el patron numerado Anterior/Siguiente de
 * Tailwind UI. Puramente presentacional: recibe la pagina actual y el numero
 * total de paginas, y emite `pageChange` al pulsar un numero o los extremos.
 * No conoce de donde vienen los datos ni como se cargan.
 */
@Component({
  selector: 'app-pagination',
  standalone: true,
  templateUrl: './pagination.html',
})
export class PaginationComponent {
  /** Pagina actual, 1-based. */
  readonly page = input.required<number>();
  /** Numero total de paginas (>= 1). */
  readonly totalPages = input.required<number>();
  readonly pageChange = output<number>();

  readonly pages = computed(() => Array.from({ length: this.totalPages() }, (_, i) => i + 1));

  goTo(target: number): void {
    if (target < 1 || target > this.totalPages() || target === this.page()) {
      return;
    }
    this.pageChange.emit(target);
  }
}
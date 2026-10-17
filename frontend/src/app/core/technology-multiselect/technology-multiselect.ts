import {
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  computed,
  effect,
  inject,
  input,
  model,
  signal,
  viewChild,
} from '@angular/core';
import { Technology } from '../generations-api.model';

let nextListboxId = 0;

/**
 * Selector multiple determinista de tecnologias del catalogo (change
 * `catalogo-tecnologias`, tarea 5.1; design.md D5). Combobox accesible con
 * busqueda: el trigger muestra las tecnologias seleccionadas como chips y el
 * panel ofrece un buscador y una lista de checkboxes del catalogo. No permite
 * anadir texto libre -- solo seleccionar lo que llega en `technologies`.
 */
@Component({
  selector: 'app-technology-multiselect',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './technology-multiselect.html',
  host: { '(document:click)': 'onDocumentClick($event)' },
})
export class TechnologyMultiselectComponent {
  /** Catalogo de tecnologias disponibles. */
  readonly technologies = input<Technology[]>([]);
  readonly loading = input(false);
  readonly error = input(false);
  /** Id del elemento que etiqueta el combobox (accesibilidad); opcional. */
  readonly labelledby = input<string | null>(null);

  /** Nombres canonicos seleccionados (two-way: `[(selected)]`). */
  readonly selected = model<string[]>([]);

  readonly open = signal(false);
  readonly search = signal('');
  readonly activeIndex = signal(-1);
  readonly listboxId = `tech-listbox-${nextListboxId++}`;

  private readonly elementRef = inject(ElementRef);
  private readonly searchInput = viewChild<ElementRef<HTMLInputElement>>('searchInput');

  readonly filtered = computed(() => {
    const term = this.search().trim().toLowerCase();
    const all = this.technologies();
    return term ? all.filter((t) => t.name.toLowerCase().includes(term)) : all;
  });

  readonly activeOptionId = computed(() => {
    const index = this.activeIndex();
    const options = this.filtered();
    return index >= 0 && index < options.length ? this.optionId(options[index]) : null;
  });

  constructor() {
    effect(() => {
      const el = this.searchInput();
      if (this.open() && el) {
        el.nativeElement.focus();
      }
    });
  }

  optionId(tech: Technology): string {
    return `${this.listboxId}-${tech.id}`;
  }

  optionClass(index: number): string {
    const base =
      'flex cursor-pointer items-center gap-2 rounded-md px-3 py-2 text-sm text-content hover:bg-primary/10';
    return index === this.activeIndex() ? `${base} bg-primary/10` : base;
  }

  isSelected(name: string): boolean {
    return this.selected().includes(name);
  }

  toggle(): void {
    const willOpen = !this.open();
    this.open.set(willOpen);
    if (willOpen) {
      this.search.set('');
      this.activeIndex.set(-1);
    }
  }

  close(): void {
    this.open.set(false);
  }

  toggleTechnology(name: string): void {
    this.selected.update((current) =>
      current.includes(name) ? current.filter((n) => n !== name) : [...current, name],
    );
  }

  remove(name: string, event: Event): void {
    event.stopPropagation();
    this.toggleTechnology(name);
  }

  onSearch(event: Event): void {
    this.search.set((event.target as HTMLInputElement).value);
    this.activeIndex.set(-1);
  }

  onKeydown(event: KeyboardEvent): void {
    const options = this.filtered();
    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        if (!this.open()) {
          this.toggle();
          return;
        }
        this.activeIndex.update((index) => Math.min(index + 1, options.length - 1));
        break;
      case 'ArrowUp':
        event.preventDefault();
        this.activeIndex.update((index) => Math.max(index - 1, 0));
        break;
      case 'Enter': {
        const index = this.activeIndex();
        if (this.open() && index >= 0 && index < options.length) {
          event.preventDefault();
          this.toggleTechnology(options[index].name);
        }
        break;
      }
      case 'Escape':
        if (this.open()) {
          event.preventDefault();
          this.close();
        }
        break;
    }
  }

  onDocumentClick(event: Event): void {
    if (this.open() && !this.elementRef.nativeElement.contains(event.target as Node)) {
      this.close();
    }
  }
}
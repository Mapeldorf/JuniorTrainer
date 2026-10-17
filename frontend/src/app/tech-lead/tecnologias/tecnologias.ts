import { Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Technology } from '../../core/generations-api.model';
import { GenerationsApiService } from '../../core/generations-api.service';
import { TechLeadNavComponent } from '../tech-lead-nav/tech-lead-nav';

/**
 * Pantalla "Tecnologías" del tech lead (change `generacion-tecnologias`,
 * capacidad technology-catalog: "Interfaz de alta de tecnologías"). Lista el
 * catálogo canónico y ofrece un formulario para dar de alta una tecnología,
 * que el backend valida con el agente juez antes de guardarla. Muestra el
 * éxito, el rechazo del validador o el aviso de duplicado.
 */
@Component({
  selector: 'app-tecnologias',
  standalone: true,
  imports: [FormsModule, TechLeadNavComponent],
  templateUrl: './tecnologias.html',
})
export class TecnologiasComponent {
  private readonly api = inject(GenerationsApiService);

  readonly technologies = signal<Technology[]>([]);
  readonly loading = signal(true);
  readonly loadError = signal(false);

  readonly name = signal('');
  readonly submitting = signal(false);
  readonly error = signal<string | null>(null);
  readonly success = signal(false);

  readonly canSubmit = computed(() => this.name().trim().length > 0 && !this.submitting());

  constructor() {
    this.load();
  }

  private load(): void {
    this.loading.set(true);
    this.loadError.set(false);
    this.api.getTechnologies().subscribe({
      next: (list) => {
        this.technologies.set(list);
        this.loading.set(false);
      },
      error: () => {
        this.loadError.set(true);
        this.loading.set(false);
      },
    });
  }

  create(): void {
    if (!this.canSubmit()) {
      return;
    }
    this.submitting.set(true);
    this.error.set(null);
    this.success.set(false);
    this.api.createTechnology(this.name().trim()).subscribe({
      next: (technology) => {
        this.technologies.update((current) =>
          [...current, technology].sort((a, b) => a.name.localeCompare(b.name)),
        );
        this.name.set('');
        this.submitting.set(false);
        this.success.set(true);
      },
      error: (err: unknown) => {
        this.submitting.set(false);
        this.error.set(this.messageFor(err));
      },
    });
  }

  /** Mensaje segun el codigo de estado del backend (design.md D1): 409
   * duplicado, 422 rechazo del validador, 502 validador no disponible. */
  private messageFor(err: unknown): string {
    const status = (err as { status?: number } | null)?.status;
    if (status === 409) {
      return 'Esa tecnología ya existe en el catálogo.';
    }
    if (status === 422) {
      return 'La tecnología no se ha podido validar como tecnología de programación.';
    }
    if (status === 502) {
      return 'El validador no está disponible en este momento. Inténtalo más tarde.';
    }
    return 'No se ha podido dar de alta la tecnología.';
  }
}
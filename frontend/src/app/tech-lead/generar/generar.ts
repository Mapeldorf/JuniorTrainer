import { Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { GenerationsApiService } from '../../core/generations-api.service';
import { TechLeadNavComponent } from '../tech-lead-nav/tech-lead-nav';

const MIN_COUNT = 1;
const MAX_COUNT = 5;

/**
 * Pantalla 3 "Generar ejercicios" (tareas 5.1-5.2, capacidad
 * `exercise-generation`). Sin campo de repositorio ni selector de tipo
 * (design.md decision 5, "Goals/Non-Goals"): toda generacion de este
 * formulario es `knowledge`, porque esta parte no tiene subida de
 * repositorio.
 */
@Component({
  selector: 'app-generar',
  standalone: true,
  imports: [FormsModule, TechLeadNavComponent],
  templateUrl: './generar.html',
})
export class GenerarComponent {
  private readonly api = inject(GenerationsApiService);
  private readonly router = inject(Router);

  readonly technologies = signal<string[]>([]);
  readonly newTechnology = signal('');
  readonly count = signal(3);
  readonly submitting = signal(false);
  readonly error = signal<string | null>(null);

  readonly isValid = computed(
    () => this.technologies().length > 0 && this.count() >= MIN_COUNT && this.count() <= MAX_COUNT,
  );

  addTechnology(): void {
    const value = this.newTechnology().trim();
    if (!value || this.technologies().includes(value)) {
      this.newTechnology.set('');
      return;
    }
    this.technologies.set([...this.technologies(), value]);
    this.newTechnology.set('');
  }

  removeTechnology(value: string): void {
    this.technologies.set(this.technologies().filter((t) => t !== value));
  }

  /** Tarea 5.2: solo envia si `isValid()` -- tecnologias no vacias y
   * numero de candidatos entre 1 y 5. */
  generar(): void {
    if (!this.isValid() || this.submitting()) {
      return;
    }
    this.submitting.set(true);
    this.error.set(null);
    this.api
      .start({
        technologies: this.technologies(),
        repo_path: null,
        kind: 'knowledge',
        count: this.count(),
      })
      .subscribe({
        next: () => {
          void this.router.navigate(['/ejercicios']);
        },
        error: () => {
          this.error.set('No se ha podido iniciar la generación.');
          this.submitting.set(false);
        },
      });
  }

  cancelar(): void {
    void this.router.navigate(['/ejercicios']);
  }
}

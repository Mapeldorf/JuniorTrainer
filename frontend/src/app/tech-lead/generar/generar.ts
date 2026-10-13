import { Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { GenerationKind } from '../../core/generations-api.model';
import { GenerationsApiService } from '../../core/generations-api.service';
import { TechLeadNavComponent } from '../tech-lead-nav/tech-lead-nav';

const MIN_COUNT = 1;
const MAX_COUNT = 5;

/**
 * Pantalla 3 "Generar ejercicios" (tareas 5.1-5.2, capacidad
 * `exercise-generation`; ampliada por el change `acceso-repo-github-tool`,
 * grupo 8, para exponer el repositorio y el tipo de ejercicio -- sin eso,
 * la funcionalidad de acceso a GitHub no tenia ninguna via de entrada
 * real desde la aplicacion). `owner`/`repo` son opcionales pero deben
 * indicarse juntos (misma regla que valida el backend); sin repositorio
 * solo se puede elegir el tipo `knowledge` (requisito "Tipo de ejercicio
 * exige repositorio salvo conocimiento" de
 * `specs/exercise-generation/spec.md`).
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
  readonly owner = signal('');
  readonly repo = signal('');
  readonly kind = signal<GenerationKind>('knowledge');
  readonly count = signal(3);
  readonly submitting = signal(false);
  readonly error = signal<string | null>(null);

  /** `true` solo cuando `owner` y `repo` tienen contenido real (tras
   * recortar espacios): es lo que habilita los tipos `debug`/`both` y lo
   * que decide si se envian como `null` o como texto al backend. */
  readonly hasRepo = computed(() => this.owner().trim().length > 0 && this.repo().trim().length > 0);

  /** `owner`/`repo` deben indicarse juntos o ninguno (si solo uno tiene
   * texto, el formulario no es valido todavia). */
  private readonly ownerRepoConsistent = computed(
    () => (this.owner().trim().length > 0) === (this.repo().trim().length > 0),
  );

  readonly isValid = computed(
    () =>
      this.technologies().length > 0 &&
      this.count() >= MIN_COUNT &&
      this.count() <= MAX_COUNT &&
      this.ownerRepoConsistent() &&
      (this.hasRepo() || this.kind() === 'knowledge'),
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

  /** Si se vacía el repositorio mientras el tipo no era `knowledge`, se
   * vuelve a `knowledge` -- evita dejar seleccionado un tipo que ya no
   * sería válido sin repositorio. */
  onOwnerOrRepoChange(): void {
    if (!this.hasRepo() && this.kind() !== 'knowledge') {
      this.kind.set('knowledge');
    }
  }

  /** Tarea 8.1 (acceso-repo-github-tool): solo envia si `isValid()` --
   * tecnologias no vacias, numero de candidatos entre 1 y 5, owner/repo
   * juntos o ninguno, y tipo compatible con si hay repositorio. */
  generar(): void {
    if (!this.isValid() || this.submitting()) {
      return;
    }
    this.submitting.set(true);
    this.error.set(null);
    this.api
      .start({
        technologies: this.technologies(),
        owner: this.hasRepo() ? this.owner().trim() : null,
        repo: this.hasRepo() ? this.repo().trim() : null,
        kind: this.kind(),
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

import { Component, computed, effect, inject, input, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { forkJoin, of, switchMap } from 'rxjs';
import { GenerationsApiService } from '../../core/generations-api.service';
import { GenerationDetail } from '../../core/generations-api.model';
import { TechLeadNavComponent } from '../tech-lead-nav/tech-lead-nav';

/**
 * Pantalla 4 "Revisar generacion" (tareas 6.1-6.2, capacidades
 * `exercise-generation` y `exercise-catalog`). Ruta
 * `/ejercicios/:generationId/revisar`; `generationId` llega como
 * `input()` gracias a `withComponentInputBinding` (mismo patron que
 * `EjercicioComponent`).
 */
@Component({
  selector: 'app-revisar',
  standalone: true,
  imports: [FormsModule, TechLeadNavComponent],
  templateUrl: './revisar.html',
})
export class RevisarComponent {
  readonly generationId = input.required<string>();

  private readonly api = inject(GenerationsApiService);
  private readonly router = inject(Router);

  readonly detail = signal<GenerationDetail | null>(null);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly saving = signal(false);

  private readonly selected = signal<Record<string, boolean>>({});
  private readonly editedAnswers = signal<Record<string, string>>({});
  private readonly editedNames = signal<Record<string, string>>({});

  constructor() {
    // Igual que `EjercicioComponent`: leer `generationId()` dentro de un
    // `effect()` en vez de directamente en el constructor, porque un
    // `input.required()` lanza si se lee antes de que el binding de la
    // ruta (o `setInput` en los tests) lo haya fijado todavia.
    effect(() => {
      const generationId = this.generationId();
      this.cargarDetalle(generationId);
    });
  }

  private cargarDetalle(generationId: string): void {
    this.loading.set(true);
    this.error.set(null);
    this.api.getDetail(generationId).subscribe({
      next: (detail) => {
        this.detail.set(detail);
        const answers: Record<string, string> = {};
        const names: Record<string, string> = {};
        // Change `revisar-seleccion-confirmacion` (design.md decision 1):
        // todos los candidatos salen premarcados, no hay que marcarlos
        // uno a uno para el caso mas comun (guardar casi todos).
        const selection: Record<string, boolean> = {};
        for (const candidate of detail.candidates) {
          answers[candidate.id] = candidate.expected_answer ?? '';
          names[candidate.id] = candidate.name;
          selection[candidate.id] = true;
        }
        this.editedAnswers.set(answers);
        this.editedNames.set(names);
        this.selected.set(selection);
        this.loading.set(false);
      },
      error: () => {
        this.error.set('No se ha podido cargar la generación.');
        this.loading.set(false);
      },
    });
  }

  isSelected(candidateId: string): boolean {
    return this.selected()[candidateId] ?? false;
  }

  toggleSelected(candidateId: string): void {
    this.selected.set({ ...this.selected(), [candidateId]: !this.isSelected(candidateId) });
  }

  /** Change `revisar-seleccion-confirmacion` (design.md decision 2):
   * `true` solo si hay candidatos y todos estan marcados -- refleja el
   * estado del checkbox "Seleccionar todos" en la plantilla. */
  readonly allSelected = computed(() => {
    const candidates = this.detail()?.candidates ?? [];
    return candidates.length > 0 && candidates.every((c) => this.isSelected(c.id));
  });

  /** Si todo esta marcado, desmarca todos; si no, marca todos. */
  toggleAll(): void {
    const candidates = this.detail()?.candidates ?? [];
    const markAll = !this.allSelected();
    const selection: Record<string, boolean> = {};
    for (const candidate of candidates) {
      selection[candidate.id] = markAll;
    }
    this.selected.set(selection);
  }

  answerFor(candidateId: string): string {
    return this.editedAnswers()[candidateId] ?? '';
  }

  setAnswer(candidateId: string, value: string): void {
    this.editedAnswers.set({ ...this.editedAnswers(), [candidateId]: value });
  }

  /** Change `ejercicios-con-nombre`: mismo patron que `answerFor`/
   * `setAnswer`, para el nombre editable de cada candidato. */
  nameFor(candidateId: string): string {
    return this.editedNames()[candidateId] ?? '';
  }

  setName(candidateId: string, value: string): void {
    this.editedNames.set({ ...this.editedNames(), [candidateId]: value });
  }

  /** Tarea 6.2: guarda solo los candidatos marcados (con su respuesta
   * esperada y/o su nombre editados si cambiaron -- se omite cada campo
   * si no cambio, para conservar el original, design.md decision 4;
   * extendido al nombre por el change `ejercicios-con-nombre`), y
   * despues cierra la revision; funciona igual con 0 candidatos
   * marcados (requisito "Cerrar la revision con candidatos sin
   * guardar"). */
  guardar(): void {
    if (this.saving()) {
      return;
    }
    const candidates = this.detail()?.candidates ?? [];
    const marked = candidates.filter((c) => this.isSelected(c.id));

    // Change `revisar-seleccion-confirmacion` (design.md decision 3): si
    // queda algun candidato sin marcar, se pierde para siempre al cerrar
    // la revision -- se avisa antes de proceder. Si todo esta marcado no
    // hay nada que perder y se omite el aviso (comportamiento sin cambios).
    const unmarkedCount = candidates.length - marked.length;
    if (unmarkedCount > 0 && !this.confirmarPerdida(unmarkedCount)) {
      return;
    }

    this.saving.set(true);
    this.error.set(null);

    const saveRequests = marked.map((candidate) => {
      const editedAnswer = this.answerFor(candidate.id);
      const originalAnswer = candidate.expected_answer ?? '';
      const editedName = this.nameFor(candidate.id);
      return this.api.save(candidate.id, {
        expected_answer: editedAnswer !== originalAnswer ? editedAnswer : undefined,
        name: editedName !== candidate.name ? editedName : undefined,
      });
    });

    (saveRequests.length > 0 ? forkJoin(saveRequests) : of([]))
      .pipe(switchMap(() => this.api.close(this.generationId())))
      .subscribe({
        next: () => void this.router.navigate(['/ejercicios']),
        error: () => {
          this.error.set('No se han podido guardar los ejercicios.');
          this.saving.set(false);
        },
      });
  }

  cancelar(): void {
    void this.router.navigate(['/ejercicios']);
  }

  /** Envuelto en un metodo propio (mismo patron que `confirmarEliminar()`
   * en `ejercicios.ts`/`bloque-detalle.ts`) para poder sustituirlo en los
   * tests sin depender del `confirm()` global del navegador. */
  confirmarPerdida(count: number): boolean {
    const plural = count === 1 ? 'ejercicio' : 'ejercicios';
    return confirm(
      `${count} ${plural} sin marcar se van a perder para siempre. ¿Continuar y guardar solo los marcados?`,
    );
  }

  statusMessage(detail: GenerationDetail): string {
    if (detail.status === 'generating') {
      return 'La generación todavía está en curso.';
    }
    if (detail.status === 'error') {
      return detail.error_message ?? 'La generación ha fallado.';
    }
    return '';
  }

}

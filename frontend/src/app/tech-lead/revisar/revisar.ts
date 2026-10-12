import { Component, effect, inject, input, signal } from '@angular/core';
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
        for (const candidate of detail.candidates) {
          answers[candidate.id] = candidate.expected_answer ?? '';
        }
        this.editedAnswers.set(answers);
        this.selected.set({});
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

  answerFor(candidateId: string): string {
    return this.editedAnswers()[candidateId] ?? '';
  }

  setAnswer(candidateId: string, value: string): void {
    this.editedAnswers.set({ ...this.editedAnswers(), [candidateId]: value });
  }

  /** Tarea 6.2: guarda solo los candidatos marcados (con su respuesta
   * esperada editada si cambio -- se omite el campo si no cambio, para
   * conservar la original, design.md decision 4), y despues cierra la
   * revision; funciona igual con 0 candidatos marcados (requisito
   * "Cerrar la revision con candidatos sin guardar"). */
  guardar(): void {
    if (this.saving()) {
      return;
    }
    const candidates = this.detail()?.candidates ?? [];
    const marked = candidates.filter((c) => this.isSelected(c.id));

    this.saving.set(true);
    this.error.set(null);

    const saveRequests = marked.map((candidate) => {
      const edited = this.answerFor(candidate.id);
      const original = candidate.expected_answer ?? '';
      return this.api.save(candidate.id, edited !== original ? edited : undefined);
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

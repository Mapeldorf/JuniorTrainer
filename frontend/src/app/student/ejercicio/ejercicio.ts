import { Component, computed, effect, inject, input, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AssignmentsApiService } from '../../core/assignments-api.service';
import { AssignmentDetail, Verdict } from '../../core/assignments-api.model';
import { BrandMarkComponent } from '../../core/brand-mark';
import { NoCopyPasteDirective } from '../../core/no-copy-paste.directive';

/**
 * Pantallas 9 "Ejercicio" y 10 "Valoracion" (tareas 4.2-4.5, capacidades
 * `student-assignments` y `answer-evaluation`): un unico componente para
 * las dos, porque solo difieren en si el ejercicio de esta posicion ya
 * tiene respuesta (ver design.md - Decisions). Ruta
 * `/mis-bloques/:assignmentId/ejercicios/:position` (1-based); los
 * parametros llegan como `input()` gracias a `withComponentInputBinding`
 * (ver app.config.ts).
 */
@Component({
  selector: 'app-ejercicio',
  standalone: true,
  imports: [FormsModule, RouterLink, BrandMarkComponent, NoCopyPasteDirective],
  templateUrl: './ejercicio.html',
})
export class EjercicioComponent {
  readonly assignmentId = input.required<string>();
  readonly position = input.required<string>();

  private readonly assignmentsApi = inject(AssignmentsApiService);
  private readonly router = inject(Router);

  readonly detail = signal<AssignmentDetail | null>(null);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);

  readonly answerText = signal('');
  readonly submitting = signal(false);
  readonly submitError = signal<string | null>(null);

  readonly positionNumber = computed(() => Number(this.position()));

  readonly exercise = computed(() => {
    const detail = this.detail();
    if (!detail) {
      return null;
    }
    return detail.exercises.find((e) => e.position === this.positionNumber()) ?? null;
  });

  /** Ultima posicion visible para esta asignacion: el detalle del
   * backend ya corta en el primer ejercicio sin responder (tarea 1.3),
   * asi que su longitud es el limite de "Siguiente" y de la barra de
   * pasos / selector. */
  readonly maxPosition = computed(() => this.detail()?.exercises.length ?? 0);

  readonly visiblePositions = computed(() => this.detail()?.exercises.map((e) => e.position) ?? []);

  /** Mas de 10 ejercicios: selector en vez de barra de pasos (tarea 4.5,
   * seccion 10 de la especificacion). */
  readonly useSelector = computed(() => this.maxPosition() > 10);

  constructor() {
    // Solo depende de `assignmentId`: el detalle se recarga por
    // asignacion, no por posicion (design.md - Decisions). Las lecturas
    // de senales dentro de `effect()` que determinan sus dependencias
    // son solo las de este bloque, asi que cambiar de posicion no
    // vuelve a disparar la carga.
    effect(() => {
      const assignmentId = this.assignmentId();
      this.cargarDetalle(assignmentId);
    });
  }

  private cargarDetalle(assignmentId: string): void {
    this.loading.set(true);
    this.error.set(null);
    this.assignmentsApi.getDetail(assignmentId).subscribe({
      next: (detail) => {
        this.detail.set(detail);
        this.loading.set(false);
        this.answerText.set('');
      },
      error: () => {
        this.error.set('No se ha podido cargar este ejercicio.');
        this.loading.set(false);
      },
    });
  }

  enviar(): void {
    const exercise = this.exercise();
    const text = this.answerText().trim();
    if (!exercise || !text || this.submitting()) {
      return;
    }

    this.submitting.set(true);
    this.submitError.set(null);
    this.assignmentsApi.submitAnswer(this.assignmentId(), exercise.exercise_id, text).subscribe({
      next: () => {
        this.submitting.set(false);
        // tarea 4.3: tras enviar, se vuelve a pedir el detalle en vez de
        // parchear el estado local (design.md - Decisions), para pasar a
        // la variante de valoracion con los datos reales y, si lo hay,
        // recoger el siguiente ejercicio desbloqueado.
        this.cargarDetalle(this.assignmentId());
      },
      error: (err: { status?: number }) => {
        this.submitting.set(false);
        if (err?.status === 409) {
          // tarea 4.7: ya respondido (p. ej. desde otra pestana) --
          // resincroniza en vez de mostrar un error sin manejar.
          this.cargarDetalle(this.assignmentId());
          return;
        }
        this.submitError.set('No se ha podido evaluar tu respuesta. Inténtalo de nuevo.');
      },
    });
  }

  anterior(): void {
    const target = this.positionNumber() - 1;
    if (target >= 1) {
      this.irA(target);
    }
  }

  siguiente(): void {
    const target = this.positionNumber() + 1;
    if (target <= this.maxPosition()) {
      this.irA(target);
    }
  }

  irA(position: number): void {
    void this.router.navigate(['/mis-bloques', this.assignmentId(), 'ejercicios', position]);
  }

  onSelectorChange(event: Event): void {
    const value = Number((event.target as HTMLSelectElement).value);
    if (value) {
      this.irA(value);
    }
  }

  verdictLabel(verdict: Verdict | null): string {
    switch (verdict) {
      case 'correct':
        return 'Correcta';
      case 'incomplete':
        return 'Incompleta';
      case 'incorrect':
        return 'Incorrecta';
      default:
        return '';
    }
  }
}

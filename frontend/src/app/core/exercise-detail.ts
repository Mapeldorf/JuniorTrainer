import { Component, ElementRef, effect, input, output, viewChild } from '@angular/core';
import { SavedExerciseListItem } from './generations-api.model';

/**
 * Panel de detalle de un ejercicio guardado (change
 * `detalle-ejercicio-guardado`, capacidad `exercise-catalog`). Modal
 * centrado con cuerpo desplazable, montado por la pantalla de guardados.
 * Puramente presentacional: recibe el ejercicio a mostrar y emite el
 * cierre; no conoce de donde vienen los datos. El contenido es de solo
 * lectura.
 *
 * Teclado/accesibilidad: el foco inicial recae en el boton de cierre y
 * Escape cierra el panel, igual que `confirm-dialog`.
 */
@Component({
  selector: 'app-exercise-detail',
  standalone: true,
  templateUrl: './exercise-detail.html',
})
export class ExerciseDetailComponent {
  readonly exercise = input<SavedExerciseListItem | null>(null);
  readonly closed = output<void>();

  private readonly closeButton = viewChild<ElementRef<HTMLButtonElement>>('closeButton');

  constructor() {
    effect(() => {
      const exercise = this.exercise();
      const button = this.closeButton();
      if (exercise && button) {
        button.nativeElement.focus();
      }
    });
  }

  typeLabel(type: SavedExerciseListItem['type']): string {
    return type === 'knowledge' ? 'Conocimiento' : 'Depuración';
  }

  close(): void {
    this.closed.emit();
  }
}
import { Component, ElementRef, effect, inject, viewChild } from '@angular/core';
import { ConfirmDialogService } from './confirm-dialog.service';

/**
 * Dialogo de confirmacion propio de la app (change
 * `dialogo-confirmacion-tailwind`, capacidad `confirm-dialog`), montado
 * una vez en `app.html`. Sustituye a `window.confirm()`: no renderiza
 * nada mientras `ConfirmDialogService.request()` es `null`.
 *
 * Teclado (requisito "Cierre con teclado"): el foco inicial recae en el
 * boton de cancelar en cuanto se abre (evita confirmar una accion
 * destructiva sin querer al pulsar Enter), y Escape cancela igual que el
 * boton.
 */
@Component({
  selector: 'app-confirm-dialog',
  standalone: true,
  templateUrl: './confirm-dialog.html',
})
export class ConfirmDialogComponent {
  protected readonly service = inject(ConfirmDialogService);

  private readonly cancelButton = viewChild<ElementRef<HTMLButtonElement>>('cancelButton');

  constructor() {
    effect(() => {
      const request = this.service.request();
      const button = this.cancelButton();
      if (request && button) {
        button.nativeElement.focus();
      }
    });
  }

  confirm(): void {
    this.service.resolveConfirm();
  }

  cancel(): void {
    this.service.resolveCancel();
  }
}

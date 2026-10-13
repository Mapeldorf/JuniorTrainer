import { Injectable, signal } from '@angular/core';
import { ConfirmDialogRequest } from './confirm-dialog.model';

/**
 * Servicio compartido del dialogo de confirmacion (change
 * `dialogo-confirmacion-tailwind`, capacidad `confirm-dialog`): sustituye
 * a `window.confirm()` en toda la app. `confirm()` fija la peticion
 * actual (leida por `ConfirmDialogComponent`, montado una vez en
 * `app.html`) y devuelve una promesa que se resuelve cuando el usuario
 * confirma o cancela -- un dialogo en pantalla no puede bloquear de
 * forma sincrona como el `confirm()` nativo (design.md - Decisions).
 *
 * Sin diálogos anidados (Non-Goals de design.md): si `confirm()` se
 * llama con una peticion ya activa, esa peticion anterior se resuelve
 * como cancelada (`false`) antes de mostrar la nueva, para no dejar su
 * promesa colgada para siempre.
 */
@Injectable({ providedIn: 'root' })
export class ConfirmDialogService {
  readonly request = signal<ConfirmDialogRequest | null>(null);

  private pendingResolve: ((value: boolean) => void) | null = null;

  confirm(options: ConfirmDialogRequest): Promise<boolean> {
    this.resolveCancel();
    return new Promise<boolean>((resolve) => {
      this.pendingResolve = resolve;
      this.request.set(options);
    });
  }

  resolveConfirm(): void {
    this.settle(true);
  }

  resolveCancel(): void {
    this.settle(false);
  }

  private settle(value: boolean): void {
    const resolve = this.pendingResolve;
    if (!resolve) {
      return;
    }
    this.pendingResolve = null;
    this.request.set(null);
    resolve(value);
  }
}

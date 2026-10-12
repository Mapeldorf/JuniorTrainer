import { Directive, HostListener } from '@angular/core';

/**
 * Cancela copiar, cortar, pegar, arrastrar y el menu contextual sobre el
 * elemento al que se aplica (tarea 4.1, seccion 3 de la especificacion):
 * friccion deliberada en el enunciado/codigo y en el cuadro de respuesta,
 * "hasta donde el navegador lo permita" -- no es, ni pretende ser, una
 * garantia de seguridad (ver design.md - Risks / Trade-offs).
 */
@Directive({
  selector: '[appNoCopyPaste]',
  standalone: true,
})
export class NoCopyPasteDirective {
  @HostListener('copy', ['$event'])
  @HostListener('cut', ['$event'])
  @HostListener('paste', ['$event'])
  @HostListener('dragstart', ['$event'])
  @HostListener('contextmenu', ['$event'])
  onBlockedEvent(event: Event): void {
    event.preventDefault();
  }
}

import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { SupabaseService } from './supabase.service';

/**
 * Decide el destino post-login por rol en la ruta raiz (tarea 2.4 de
 * frontend-tech-lead-ejercicios, actualizando la de frontend-alumno;
 * design.md - Decisions): un alumno va a "Mis bloques de ejercicios", un
 * tech lead va a "Ejercicios guardados" (ya no se queda en el `home`
 * placeholder), y cualquier otro caso (sin rol reconocido) se deja pasar.
 * No comprueba la sesion por su cuenta -- eso ya lo exige `authGuard`,
 * con el que esta guard se combina en la ruta `''`.
 */
export const homeRedirectGuard: CanActivateFn = async () => {
  const supabase = inject(SupabaseService);
  const router = inject(Router);

  const role = await supabase.getRole();
  if (role === 'student') {
    return router.createUrlTree(['/mis-bloques']);
  }
  if (role === 'tech_lead') {
    return router.createUrlTree(['/ejercicios']);
  }
  return true;
};

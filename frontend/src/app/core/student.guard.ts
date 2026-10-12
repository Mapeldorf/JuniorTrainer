import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { SupabaseService } from './supabase.service';

/**
 * Exige rol `student` (tarea 2.4). Sin sesion, manda a login (igual que
 * `authGuard`, con el que se combina en las rutas de alumno); con sesion
 * pero sin ese rol (tech lead), manda a `/`.
 */
export const studentGuard: CanActivateFn = async () => {
  const supabase = inject(SupabaseService);
  const router = inject(Router);

  const role = await supabase.getRole();
  if (role === 'student') {
    return true;
  }
  if (role === null) {
    return router.createUrlTree(['/login']);
  }
  return router.createUrlTree(['/']);
};

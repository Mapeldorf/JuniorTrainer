import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { SupabaseService } from './supabase.service';

/**
 * Exige rol `tech_lead` (tarea 2.3, mismo patron que `studentGuard`).
 * Sin sesion, manda a login; con sesion pero sin ese rol (alumno), manda
 * a `/`.
 */
export const techLeadGuard: CanActivateFn = async () => {
  const supabase = inject(SupabaseService);
  const router = inject(Router);

  const role = await supabase.getRole();
  if (role === 'tech_lead') {
    return true;
  }
  if (role === null) {
    return router.createUrlTree(['/login']);
  }
  return router.createUrlTree(['/']);
};

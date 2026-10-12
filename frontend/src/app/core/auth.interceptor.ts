import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { from, switchMap } from 'rxjs';
import { environment } from '../../environments/environment';
import { SupabaseService } from './supabase.service';

/**
 * Antepone el JWT de la sesion de Supabase a toda peticion dirigida a
 * FastAPI (tarea 2.2, capacidades `student-assignments` y
 * `answer-evaluation`). No toca ninguna otra peticion: el SDK de
 * Supabase hace las suyas por su cuenta, sin pasar por `HttpClient`, pero
 * se comprueba el prefijo de la URL de todas formas por si alguna otra
 * peticion ajena a FastAPI llegara a pasar por aqui (ver design.md -
 * Decisions).
 */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  if (!req.url.startsWith(environment.apiUrl)) {
    return next(req);
  }

  const supabase = inject(SupabaseService);

  return from(supabase.getSession()).pipe(
    switchMap((session) => {
      if (!session) {
        return next(req);
      }
      const authReq = req.clone({
        setHeaders: { Authorization: `Bearer ${session.access_token}` },
      });
      return next(authReq);
    }),
  );
};

import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, from, switchMap, throwError } from 'rxjs';
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
 *
 * Si el backend rechaza el token con 401 pese a que `getSession()` lo
 * diera por valido (el access token caduco justo antes de llegar, o
 * Supabase lo invalido por otra razon), se fuerza una renovacion y se
 * reintenta la peticion una sola vez con el token nuevo. Si la renovacion
 * tambien falla (la sesion ya esta muerta de verdad, no solo caducada),
 * se cierra sesion y se manda a login en vez de dejar el 401 silencioso.
 */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  if (!req.url.startsWith(environment.apiUrl)) {
    return next(req);
  }

  const supabase = inject(SupabaseService);
  const router = inject(Router);

  return from(supabase.getSession()).pipe(
    switchMap((session) => {
      if (!session) {
        return next(req);
      }
      const authReq = req.clone({
        setHeaders: { Authorization: `Bearer ${session.access_token}` },
      });
      return next(authReq).pipe(
        catchError((error: unknown) => {
          if (!(error instanceof HttpErrorResponse) || error.status !== 401) {
            return throwError(() => error);
          }
          return from(supabase.refreshSession()).pipe(
            switchMap((refreshed) => {
              if (!refreshed) {
                return from(supabase.signOut()).pipe(
                  switchMap(() => {
                    void router.navigate(['/login']);
                    return throwError(() => error);
                  }),
                );
              }
              const retryReq = req.clone({
                setHeaders: { Authorization: `Bearer ${refreshed.access_token}` },
              });
              return next(retryReq);
            }),
          );
        }),
      );
    }),
  );
};

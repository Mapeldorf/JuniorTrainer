import { Routes } from '@angular/router';
import { authGuard } from './core/auth.guard';
import { homeRedirectGuard } from './core/home-redirect.guard';
import { studentGuard } from './core/student.guard';
import { techLeadGuard } from './core/tech-lead.guard';

export const routes: Routes = [
  {
    path: 'ejercicios',
    canActivate: [authGuard, techLeadGuard],
    loadComponent: () =>
      import('./tech-lead/ejercicios/ejercicios').then((m) => m.EjerciciosComponent),
  },
  {
    path: 'ejercicios/generar',
    canActivate: [authGuard, techLeadGuard],
    loadComponent: () => import('./tech-lead/generar/generar').then((m) => m.GenerarComponent),
  },
  {
    path: 'ejercicios/:generationId/revisar',
    canActivate: [authGuard, techLeadGuard],
    loadComponent: () => import('./tech-lead/revisar/revisar').then((m) => m.RevisarComponent),
  },
  {
    path: 'mis-bloques',
    canActivate: [authGuard, studentGuard],
    loadComponent: () =>
      import('./student/mis-bloques/mis-bloques').then((m) => m.MisBloquesComponent),
  },
  {
    path: 'mis-bloques/:assignmentId/ejercicios/:position',
    canActivate: [authGuard, studentGuard],
    loadComponent: () =>
      import('./student/ejercicio/ejercicio').then((m) => m.EjercicioComponent),
  },
  {
    path: 'login',
    loadComponent: () => import('./auth/login/login').then((m) => m.LoginComponent),
  },
  {
    path: 'forgot',
    loadComponent: () => import('./auth/forgot/forgot').then((m) => m.ForgotComponent),
  },
  {
    path: 'set-password',
    loadComponent: () =>
      import('./auth/set-password/set-password').then((m) => m.SetPasswordComponent),
  },
  {
    path: '',
    // tarea 2.5 (frontend-alumno) y 2.4 (frontend-tech-lead-ejercicios):
    // un alumno autenticado se redirige a "Mis bloques de ejercicios", un
    // tech lead a "Ejercicios guardados" (design.md - Decisions de cada
    // change); el `home` placeholder solo se ve ya si ningun rol
    // reconocido aplica.
    canActivate: [authGuard, homeRedirectGuard],
    loadComponent: () => import('./home/home').then((m) => m.HomeComponent),
  },
  { path: '**', redirectTo: '' },
];

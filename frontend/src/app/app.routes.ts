import { Routes } from '@angular/router';
import { authGuard } from './core/auth.guard';
import { homeRedirectGuard } from './core/home-redirect.guard';
import { studentGuard } from './core/student.guard';

export const routes: Routes = [
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
    // tarea 2.5: un alumno autenticado se redirige a "Mis bloques de
    // ejercicios" (design.md - Decisions); un tech lead se queda aqui.
    canActivate: [authGuard, homeRedirectGuard],
    loadComponent: () => import('./home/home').then((m) => m.HomeComponent),
  },
  { path: '**', redirectTo: '' },
];

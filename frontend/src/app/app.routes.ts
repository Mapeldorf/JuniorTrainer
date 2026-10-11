import { Routes } from '@angular/router';
import { authGuard } from './core/auth.guard';

export const routes: Routes = [
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
    canActivate: [authGuard],
    loadComponent: () => import('./home/home').then((m) => m.HomeComponent),
  },
  { path: '**', redirectTo: '' },
];

import { authGuard } from './core/auth.guard';
import { homeRedirectGuard } from './core/home-redirect.guard';
import { studentGuard } from './core/student.guard';
import { routes } from './app.routes';

describe('routes', () => {
  it('la ruta raiz usa authGuard y homeRedirectGuard, en ese orden', () => {
    const root = routes.find((r) => r.path === '');
    expect(root).toBeTruthy();
    expect(root!.canActivate).toEqual([authGuard, homeRedirectGuard]);
  });

  it('mis-bloques y la ruta de ejercicio usan authGuard y studentGuard', () => {
    const misBloques = routes.find((r) => r.path === 'mis-bloques');
    const ejercicio = routes.find((r) => r.path === 'mis-bloques/:assignmentId/ejercicios/:position');
    expect(misBloques?.canActivate).toEqual([authGuard, studentGuard]);
    expect(ejercicio?.canActivate).toEqual([authGuard, studentGuard]);
  });
});

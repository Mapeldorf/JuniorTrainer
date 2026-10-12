import { authGuard } from './core/auth.guard';
import { homeRedirectGuard } from './core/home-redirect.guard';
import { studentGuard } from './core/student.guard';
import { techLeadGuard } from './core/tech-lead.guard';
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

  it('ejercicios y ejercicios/generar usan authGuard y techLeadGuard', () => {
    const ejercicios = routes.find((r) => r.path === 'ejercicios');
    const generar = routes.find((r) => r.path === 'ejercicios/generar');
    expect(ejercicios?.canActivate).toEqual([authGuard, techLeadGuard]);
    expect(generar?.canActivate).toEqual([authGuard, techLeadGuard]);
  });

  it('ejercicios/:generationId/revisar usa authGuard y techLeadGuard', () => {
    const revisar = routes.find((r) => r.path === 'ejercicios/:generationId/revisar');
    expect(revisar?.canActivate).toEqual([authGuard, techLeadGuard]);
  });
});

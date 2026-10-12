import { TestBed } from '@angular/core/testing';
import { provideRouter, UrlTree } from '@angular/router';
import { homeRedirectGuard } from './home-redirect.guard';
import { SupabaseService } from './supabase.service';

describe('homeRedirectGuard', () => {
  function run(getRole: () => Promise<'tech_lead' | 'student' | null>) {
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        { provide: SupabaseService, useValue: { getRole } },
      ],
    });
    return TestBed.runInInjectionContext(() => homeRedirectGuard({} as never, {} as never));
  }

  it('redirige a /mis-bloques a un alumno', async () => {
    const result = await run(async () => 'student');
    expect(result instanceof UrlTree).toBe(true);
    expect((result as UrlTree).toString()).toBe('/mis-bloques');
  });

  it('deja pasar a un tech lead', async () => {
    const result = await run(async () => 'tech_lead');
    expect(result).toBe(true);
  });

  it('deja pasar si no hay rol (lo resuelve authGuard por separado)', async () => {
    const result = await run(async () => null);
    expect(result).toBe(true);
  });
});

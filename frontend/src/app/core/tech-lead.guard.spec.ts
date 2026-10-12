import { TestBed } from '@angular/core/testing';
import { provideRouter, UrlTree } from '@angular/router';
import { techLeadGuard } from './tech-lead.guard';
import { SupabaseService } from './supabase.service';

describe('techLeadGuard', () => {
  function run(getRole: () => Promise<'tech_lead' | 'student' | null>) {
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        { provide: SupabaseService, useValue: { getRole } },
      ],
    });
    return TestBed.runInInjectionContext(() => techLeadGuard({} as never, {} as never));
  }

  it('deja pasar a un tech lead', async () => {
    const result = await run(async () => 'tech_lead');
    expect(result).toBe(true);
  });

  it('redirige a /login sin sesion', async () => {
    const result = await run(async () => null);
    expect(result instanceof UrlTree).toBe(true);
    expect((result as UrlTree).toString()).toBe('/login');
  });

  it('redirige a / a un alumno', async () => {
    const result = await run(async () => 'student');
    expect(result instanceof UrlTree).toBe(true);
    expect((result as UrlTree).toString()).toBe('/');
  });
});

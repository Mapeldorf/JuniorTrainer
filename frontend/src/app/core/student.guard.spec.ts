import { TestBed } from '@angular/core/testing';
import { Router, UrlTree } from '@angular/router';
import { provideRouter } from '@angular/router';
import { studentGuard } from './student.guard';
import { SupabaseService } from './supabase.service';

describe('studentGuard', () => {
  function run(getRole: () => Promise<'tech_lead' | 'student' | null>) {
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        { provide: SupabaseService, useValue: { getRole } },
      ],
    });
    return TestBed.runInInjectionContext(() => studentGuard({} as never, {} as never));
  }

  it('deja pasar a un alumno', async () => {
    const result = await run(async () => 'student');
    expect(result).toBe(true);
  });

  it('redirige a /login sin sesion', async () => {
    const result = await run(async () => null);
    expect(result instanceof UrlTree).toBe(true);
    expect((result as UrlTree).toString()).toBe('/login');
  });

  it('redirige a / a un tech lead', async () => {
    const result = await run(async () => 'tech_lead');
    expect(result instanceof UrlTree).toBe(true);
    expect((result as UrlTree).toString()).toBe('/');
  });
});

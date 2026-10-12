import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { TechLeadNavComponent } from './tech-lead-nav';
import { SupabaseService } from '../../core/supabase.service';

describe('TechLeadNavComponent', () => {
  function createComponent() {
    TestBed.configureTestingModule({
      imports: [TechLeadNavComponent],
      providers: [
        provideRouter([]),
        { provide: SupabaseService, useValue: { signOut: async () => undefined } },
      ],
    });
    const fixture = TestBed.createComponent(TechLeadNavComponent);
    fixture.detectChanges();
    return fixture;
  }

  it('"Ejercicios guardados" es un enlace a /ejercicios', () => {
    const fixture = createComponent();
    const el = fixture.nativeElement as HTMLElement;
    const links = el.querySelectorAll('a');
    const link = Array.from(links).find((a) => a.textContent?.includes('Ejercicios guardados'));
    expect(link).toBeTruthy();
    expect(link!.getAttribute('routerLink') ?? link!.getAttribute('href')).toContain('/ejercicios');
  });

  it('"Bloques de ejercicios" es un enlace a /bloques (tarea 6.1)', () => {
    const fixture = createComponent();
    const el = fixture.nativeElement as HTMLElement;
    const links = el.querySelectorAll('a');
    const link = Array.from(links).find((a) => a.textContent?.includes('Bloques de ejercicios'));
    expect(link).toBeTruthy();
    expect(link!.getAttribute('routerLink') ?? link!.getAttribute('href')).toContain('/bloques');
  });

  it('"Alumnos" sigue sin ser clicable: sin <a>, con aria-disabled', () => {
    const fixture = createComponent();
    const el = fixture.nativeElement as HTMLElement;

    // Solo "Alumnos" sigue deshabilitada; las otras dos ya son <a>.
    const links = el.querySelectorAll('a');
    expect(links.length).toBe(2);

    const disabled = el.querySelectorAll('[aria-disabled="true"]');
    expect(disabled.length).toBe(1);
    expect(disabled[0].textContent).toContain('Alumnos');
    expect(disabled[0].tagName.toLowerCase()).not.toBe('a');
  });

  it('la pestana deshabilitada muestra "Próximamente"', () => {
    const fixture = createComponent();
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Próximamente');
  });

  it('incluye "Cerrar sesión"', () => {
    const fixture = createComponent();
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Cerrar sesión');
  });
});

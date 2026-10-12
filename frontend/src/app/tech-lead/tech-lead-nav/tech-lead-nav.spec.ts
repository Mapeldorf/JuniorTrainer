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
    const link = el.querySelector('a');
    expect(link).toBeTruthy();
    expect(link!.getAttribute('routerLink') ?? link!.getAttribute('href')).toContain('/ejercicios');
    expect(link!.textContent).toContain('Ejercicios guardados');
  });

  it('"Bloques de ejercicios" y "Alumnos" no son clicables: sin <a>, con aria-disabled', () => {
    const fixture = createComponent();
    const el = fixture.nativeElement as HTMLElement;

    // Ninguna de las dos pestanas deshabilitadas debe ser un <a> (ni
    // tener routerLink), solo la activa lo es.
    const links = el.querySelectorAll('a');
    expect(links.length).toBe(1);

    const disabled = el.querySelectorAll('[aria-disabled="true"]');
    expect(disabled.length).toBe(2);
    const disabledText = Array.from(disabled).map((n) => n.textContent ?? '').join(' ');
    expect(disabledText).toContain('Bloques de ejercicios');
    expect(disabledText).toContain('Alumnos');
    disabled.forEach((node) => {
      expect(node.tagName.toLowerCase()).not.toBe('a');
    });
  });

  it('las pestanas deshabilitadas muestran "Próximamente"', () => {
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

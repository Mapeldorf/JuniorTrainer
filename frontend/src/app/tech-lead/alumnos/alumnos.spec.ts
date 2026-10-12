import { HttpErrorResponse } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { of, throwError } from 'rxjs';
import { StudentSummary } from '../../core/users-api.model';
import { UsersApiService } from '../../core/users-api.service';
import { SupabaseService } from '../../core/supabase.service';
import { AlumnosComponent } from './alumnos';

const ANA: StudentSummary = { id: 's1', name: 'Ana García', email: 'ana@empresa.com' };
const LUIS: StudentSummary = { id: 's2', name: 'Luis Pérez', email: 'luis@empresa.com' };

describe('AlumnosComponent', () => {
  function createComponent(opts: {
    listStudents?: ReturnType<typeof vi.fn>;
    invite?: ReturnType<typeof vi.fn>;
  } = {}) {
    TestBed.configureTestingModule({
      imports: [AlumnosComponent],
      providers: [
        provideRouter([]),
        { provide: SupabaseService, useValue: { signOut: async () => undefined } },
        {
          provide: UsersApiService,
          useValue: {
            listStudents: opts.listStudents ?? vi.fn().mockReturnValue(of([ANA, LUIS])),
            invite: opts.invite ?? vi.fn().mockReturnValue(of({ email: 'nuevo@empresa.com', status: 'invited' })),
          },
        },
      ],
    });
    const fixture = TestBed.createComponent(AlumnosComponent);
    fixture.detectChanges();
    return fixture;
  }

  it('la tabla renderiza los alumnos de prueba con su enlace a detalle', () => {
    const fixture = createComponent();
    const el = fixture.nativeElement as HTMLElement;
    const text = el.textContent ?? '';
    expect(text).toContain('Ana García');
    expect(text).toContain('ana@empresa.com');
    expect(text).toContain('Luis Pérez');

    const router = TestBed.inject(Router);
    const navigateSpy = vi.spyOn(router, 'navigate');
    fixture.componentInstance.verDetalle(ANA);
    expect(navigateSpy).toHaveBeenCalledWith(['/alumnos', 's1']);
  });

  it('invitacion correcta: banner verde y formulario vacio', () => {
    const invite = vi.fn().mockReturnValue(of({ email: 'nuevo@empresa.com', status: 'invited' }));
    const fixture = createComponent({ invite });
    const component = fixture.componentInstance;

    component.name.set('Pablo Díaz');
    component.email.set('nuevo@empresa.com');
    component.invitar();
    fixture.detectChanges();

    expect(invite).toHaveBeenCalledWith({ name: 'Pablo Díaz', email: 'nuevo@empresa.com' });
    expect(component.banner()?.kind).toBe('success');
    expect((fixture.nativeElement as HTMLElement).textContent).toContain(
      'Invitación enviada a nuevo@empresa.com.',
    );
    expect(component.name()).toBe('');
    expect(component.email()).toBe('');
  });

  it('email duplicado (409): banner rojo y conserva lo escrito', () => {
    const invite = vi.fn().mockReturnValue(throwError(() => new HttpErrorResponse({ status: 409 })));
    const fixture = createComponent({ invite });
    const component = fixture.componentInstance;

    component.name.set('Ana García');
    component.email.set('ana@empresa.com');
    component.invitar();
    fixture.detectChanges();

    expect(component.banner()?.kind).toBe('duplicate');
    expect((fixture.nativeElement as HTMLElement).textContent).toContain(
      'Ya existe un alumno con el email ana@empresa.com.',
    );
    expect(component.name()).toBe('Ana García');
    expect(component.email()).toBe('ana@empresa.com');

    const emailInput = (fixture.nativeElement as HTMLElement).querySelector(
      'input[name="email"]',
    );
    expect(emailInput?.getAttribute('aria-invalid')).toBe('true');
  });

  it('error generico (no 409): banner generico', () => {
    const invite = vi.fn().mockReturnValue(throwError(() => new HttpErrorResponse({ status: 500 })));
    const fixture = createComponent({ invite });
    const component = fixture.componentInstance;

    component.name.set('Pablo Díaz');
    component.email.set('pablo@empresa.com');
    component.invitar();
    fixture.detectChanges();

    expect(component.banner()?.kind).toBe('error');
    expect((fixture.nativeElement as HTMLElement).textContent).toContain(
      'No se ha podido invitar al alumno.',
    );
  });
});

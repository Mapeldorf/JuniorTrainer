import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';
import { GenerationsApiService } from '../../core/generations-api.service';
import { SupabaseService } from '../../core/supabase.service';
import { TecnologiasComponent } from './tecnologias';

describe('TecnologiasComponent', () => {
  function create(
    opts: {
      getTechnologies?: ReturnType<typeof vi.fn>;
      createTechnology?: ReturnType<typeof vi.fn>;
    } = {},
  ) {
    TestBed.configureTestingModule({
      imports: [TecnologiasComponent],
      providers: [
        provideRouter([]),
        { provide: SupabaseService, useValue: { signOut: async () => undefined } },
        {
          provide: GenerationsApiService,
          useValue: {
            getTechnologies:
              opts.getTechnologies ??
              vi.fn().mockReturnValue(of([{ id: '1', name: 'Angular' }])),
            createTechnology:
              opts.createTechnology ??
              vi.fn().mockReturnValue(of({ id: '2', name: 'Vitest' })),
          },
        },
      ],
    });
    const fixture = TestBed.createComponent(TecnologiasComponent);
    fixture.detectChanges();
    return fixture;
  }

  it('carga el catálogo al iniciar', () => {
    const fixture = create();
    expect(fixture.componentInstance.technologies()).toEqual([{ id: '1', name: 'Angular' }]);
    expect(fixture.componentInstance.loading()).toBe(false);
  });

  it('sin nombre, no se envía el alta', () => {
    const createTechnology = vi.fn();
    const fixture = create({ createTechnology });

    fixture.componentInstance.name.set('   ');
    fixture.componentInstance.create();

    expect(createTechnology).not.toHaveBeenCalled();
  });

  it('el alta correcta llama a createTechnology y refresca el catálogo', () => {
    const createTechnology = vi.fn().mockReturnValue(of({ id: '2', name: 'Vitest' }));
    const fixture = create({ createTechnology });
    const component = fixture.componentInstance;

    component.name.set('Vitest');
    component.create();
    fixture.detectChanges();

    expect(createTechnology).toHaveBeenCalledWith('Vitest');
    expect(component.technologies()).toEqual([
      { id: '1', name: 'Angular' },
      { id: '2', name: 'Vitest' },
    ]);
    expect(component.success()).toBe(true);
    expect(component.name()).toBe('');
  });

  it('un rechazo del validador (422) muestra el motivo', () => {
    const createTechnology = vi.fn().mockReturnValue(throwError(() => ({ status: 422 })));
    const fixture = create({ createTechnology });
    const component = fixture.componentInstance;

    component.name.set('Cosa Rara');
    component.create();
    fixture.detectChanges();

    expect(component.error()).toContain('no se ha podido validar');
  });

  it('un duplicado (409) muestra el aviso', () => {
    const createTechnology = vi.fn().mockReturnValue(throwError(() => ({ status: 409 })));
    const fixture = create({ createTechnology });
    const component = fixture.componentInstance;

    component.name.set('Angular');
    component.create();
    fixture.detectChanges();

    expect(component.error()).toContain('ya existe');
  });
});
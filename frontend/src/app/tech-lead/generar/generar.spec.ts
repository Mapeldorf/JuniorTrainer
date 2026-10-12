import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { of, throwError } from 'rxjs';
import { GenerationsApiService } from '../../core/generations-api.service';
import { SupabaseService } from '../../core/supabase.service';
import { GenerarComponent } from './generar';

describe('GenerarComponent', () => {
  function createComponent(opts: { start?: ReturnType<typeof vi.fn> } = {}) {
    TestBed.configureTestingModule({
      imports: [GenerarComponent],
      providers: [
        provideRouter([]),
        { provide: SupabaseService, useValue: { signOut: async () => undefined } },
        {
          provide: GenerationsApiService,
          useValue: { start: opts.start ?? vi.fn().mockReturnValue(of({ id: 'g1' })) },
        },
      ],
    });
    const fixture = TestBed.createComponent(GenerarComponent);
    fixture.detectChanges();
    return fixture;
  }

  it('sin tecnologias, el formulario no es valido', () => {
    const fixture = createComponent();
    const component = fixture.componentInstance;
    component.count.set(3);
    expect(component.isValid()).toBe(false);
  });

  it('con un numero de candidatos fuera de 1-5, el formulario no es valido', () => {
    const fixture = createComponent();
    const component = fixture.componentInstance;
    component.technologies.set(['Git']);

    component.count.set(0);
    expect(component.isValid()).toBe(false);

    component.count.set(6);
    expect(component.isValid()).toBe(false);

    component.count.set(1);
    expect(component.isValid()).toBe(true);

    component.count.set(5);
    expect(component.isValid()).toBe(true);
  });

  it('generar() no llama a start() si el formulario no es valido', () => {
    const start = vi.fn().mockReturnValue(of({ id: 'g1' }));
    const fixture = createComponent({ start });
    fixture.componentInstance.generar();
    expect(start).not.toHaveBeenCalled();
  });

  it('con datos validos, generar() llama a start() con kind knowledge y repo_path null, y navega a /ejercicios', () => {
    const start = vi.fn().mockReturnValue(of({ id: 'g1' }));
    const fixture = createComponent({ start });
    const component = fixture.componentInstance;
    const router = TestBed.inject(Router);
    const navigateSpy = vi.spyOn(router, 'navigate');

    component.technologies.set(['Git', 'Python']);
    component.count.set(2);
    component.generar();

    expect(start).toHaveBeenCalledWith({
      technologies: ['Git', 'Python'],
      repo_path: null,
      kind: 'knowledge',
      count: 2,
    });
    expect(navigateSpy).toHaveBeenCalledWith(['/ejercicios']);
  });

  it('addTechnology() anade la tecnologia y vacia el campo; no admite duplicados ni vacios', () => {
    const fixture = createComponent();
    const component = fixture.componentInstance;

    component.newTechnology.set('Git');
    component.addTechnology();
    expect(component.technologies()).toEqual(['Git']);
    expect(component.newTechnology()).toBe('');

    component.newTechnology.set('Git');
    component.addTechnology();
    expect(component.technologies()).toEqual(['Git']);

    component.newTechnology.set('   ');
    component.addTechnology();
    expect(component.technologies()).toEqual(['Git']);
  });

  it('removeTechnology() quita solo la tecnologia indicada', () => {
    const fixture = createComponent();
    const component = fixture.componentInstance;
    component.technologies.set(['Git', 'Python']);

    component.removeTechnology('Git');
    expect(component.technologies()).toEqual(['Python']);
  });

  it('si start() falla, muestra un error y no navega', () => {
    const start = vi.fn().mockReturnValue(throwError(() => new Error('fallo')));
    const fixture = createComponent({ start });
    const component = fixture.componentInstance;
    const router = TestBed.inject(Router);
    const navigateSpy = vi.spyOn(router, 'navigate');

    component.technologies.set(['Git']);
    component.generar();

    expect(component.error()).not.toBeNull();
    expect(navigateSpy).not.toHaveBeenCalled();
  });

  it('cancelar() navega a /ejercicios', () => {
    const fixture = createComponent();
    const router = TestBed.inject(Router);
    const navigateSpy = vi.spyOn(router, 'navigate');

    fixture.componentInstance.cancelar();
    expect(navigateSpy).toHaveBeenCalledWith(['/ejercicios']);
  });
});

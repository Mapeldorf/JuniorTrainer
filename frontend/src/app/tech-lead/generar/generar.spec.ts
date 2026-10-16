import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { of, throwError } from 'rxjs';
import { GenerationsApiService } from '../../core/generations-api.service';
import { GenerationTrackerService } from '../../core/generation-tracker.service';
import { SupabaseService } from '../../core/supabase.service';
import { GenerarComponent } from './generar';

describe('GenerarComponent', () => {
  function createComponent(opts: { start?: ReturnType<typeof vi.fn>; tracker?: object } = {}) {
    TestBed.configureTestingModule({
      imports: [GenerarComponent],
      providers: [
        provideRouter([]),
        { provide: SupabaseService, useValue: { signOut: async () => undefined } },
        {
          provide: GenerationsApiService,
          useValue: { start: opts.start ?? vi.fn().mockReturnValue(of({ id: 'g1' })) },
        },
        {
          provide: GenerationTrackerService,
          useValue: opts.tracker ?? {
            add: vi.fn(),
            list: vi.fn().mockReturnValue([]),
            remove: vi.fn(),
          },
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

  it('con datos validos y sin repositorio, generar() llama a start() con kind knowledge y owner/repo null, y navega a /ejercicios', () => {
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
      owner: null,
      repo: null,
      kind: 'knowledge',
      count: 2,
    });
    expect(navigateSpy).toHaveBeenCalledWith(['/ejercicios']);
  });

  it('con solo owner o solo repo (no ambos), el formulario no es valido', () => {
    const fixture = createComponent();
    const component = fixture.componentInstance;
    component.technologies.set(['Git']);

    component.owner.set('acme');
    expect(component.isValid()).toBe(false);

    component.repo.set('widgets');
    expect(component.isValid()).toBe(true);
  });

  it('sin repositorio, elegir debug u both no es valido', () => {
    const fixture = createComponent();
    const component = fixture.componentInstance;
    component.technologies.set(['Git']);

    component.kind.set('debug');
    expect(component.isValid()).toBe(false);

    component.kind.set('both');
    expect(component.isValid()).toBe(false);

    component.kind.set('knowledge');
    expect(component.isValid()).toBe(true);
  });

  it('onOwnerOrRepoChange() vuelve a knowledge si se vacia el repositorio', () => {
    const fixture = createComponent();
    const component = fixture.componentInstance;
    component.owner.set('acme');
    component.repo.set('widgets');
    component.kind.set('debug');

    component.repo.set('');
    component.onOwnerOrRepoChange();

    expect(component.kind()).toBe('knowledge');
  });

  it('con repositorio y tipo debug, generar() llama a start() con owner/repo/kind reales', () => {
    const start = vi.fn().mockReturnValue(of({ id: 'g1' }));
    const fixture = createComponent({ start });
    const component = fixture.componentInstance;
    const router = TestBed.inject(Router);
    const navigateSpy = vi.spyOn(router, 'navigate');

    component.technologies.set(['Git']);
    component.owner.set('acme');
    component.repo.set('widgets');
    component.kind.set('debug');
    component.count.set(1);
    component.generar();

    expect(start).toHaveBeenCalledWith({
      technologies: ['Git'],
      owner: 'acme',
      repo: 'widgets',
      kind: 'debug',
      count: 1,
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

  it('generar() con exito registra el id devuelto en el tracker', () => {
    const start = vi.fn().mockReturnValue(of({ id: 'g42' }));
    const add = vi.fn();
    const fixture = createComponent({ start, tracker: { add, list: vi.fn().mockReturnValue([]), remove: vi.fn() } });
    const component = fixture.componentInstance;

    component.technologies.set(['Git']);
    component.generar();

    expect(add).toHaveBeenCalledWith('g42');
  });

  it('si start() falla, no registra ninguna generacion en el tracker', () => {
    const start = vi.fn().mockReturnValue(throwError(() => new Error('fallo')));
    const add = vi.fn();
    const fixture = createComponent({ start, tracker: { add, list: vi.fn().mockReturnValue([]), remove: vi.fn() } });
    const component = fixture.componentInstance;

    component.technologies.set(['Git']);
    component.generar();

    expect(add).not.toHaveBeenCalled();
  });

  it('cancelar() navega a /ejercicios', () => {
    const fixture = createComponent();
    const router = TestBed.inject(Router);
    const navigateSpy = vi.spyOn(router, 'navigate');

    fixture.componentInstance.cancelar();
    expect(navigateSpy).toHaveBeenCalledWith(['/ejercicios']);
  });
});

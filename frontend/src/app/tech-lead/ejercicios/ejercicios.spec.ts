import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { of } from 'rxjs';
import { GenerationsApiService } from '../../core/generations-api.service';
import { GenerationSummary, SavedExerciseListItem } from '../../core/generations-api.model';
import { SupabaseService } from '../../core/supabase.service';
import { EjerciciosComponent } from './ejercicios';

const GENERATING: GenerationSummary = {
  id: 'g1',
  status: 'generating',
  technologies: ['Git'],
  repo_path: null,
  kind: 'knowledge',
  error_message: null,
  created_at: '2026-01-01',
};

const READY: GenerationSummary = { ...GENERATING, status: 'ready', technologies: ['Git', 'Python'] };

const SAVED_ITEM: SavedExerciseListItem = {
  id: 'e1',
  type: 'knowledge',
  statement: 'Explica que hace git rebase',
  code: [],
  expected_answer: 'respuesta esperada',
  technologies: ['Git'],
  repo_path: null,
};

describe('EjerciciosComponent', () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  function createComponent(opts: {
    listPending?: ReturnType<typeof vi.fn>;
    listSaved?: ReturnType<typeof vi.fn>;
    deleteFn?: ReturnType<typeof vi.fn>;
  }) {
    TestBed.configureTestingModule({
      imports: [EjerciciosComponent],
      providers: [
        provideRouter([]),
        { provide: SupabaseService, useValue: { signOut: async () => undefined } },
        {
          provide: GenerationsApiService,
          useValue: {
            listPending: opts.listPending ?? vi.fn().mockReturnValue(of([])),
            listSaved: opts.listSaved ?? vi.fn().mockReturnValue(of([])),
            delete: opts.deleteFn ?? vi.fn().mockReturnValue(of(SAVED_ITEM)),
          },
        },
      ],
    });
    const fixture = TestBed.createComponent(EjerciciosComponent);
    fixture.detectChanges();
    return fixture;
  }

  it('renderiza las generaciones pendientes y los ejercicios guardados', () => {
    const fixture = createComponent({
      listPending: vi.fn().mockReturnValue(of([READY])),
      listSaved: vi.fn().mockReturnValue(of([SAVED_ITEM])),
    });
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Git, Python');
    expect(text).toContain('Por revisar');
    expect(text).toContain(SAVED_ITEM.statement);
  });

  it('sin generaciones pendientes ni guardados, muestra los mensajes vacios', () => {
    const fixture = createComponent({});
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('No hay ninguna generación pendiente');
    expect(text).toContain('No hay ningún ejercicio guardado todavía');
  });

  it('el polling se detiene en cuanto ya no hay ninguna generacion generando', () => {
    vi.useFakeTimers();
    const listPending = vi
      .fn()
      .mockReturnValueOnce(of([GENERATING]))
      .mockReturnValueOnce(of([READY]))
      .mockReturnValue(of([READY]));

    createComponent({ listPending });
    expect(listPending).toHaveBeenCalledTimes(1);

    vi.advanceTimersByTime(3000);
    expect(listPending).toHaveBeenCalledTimes(2);

    // ya no quedaba ninguna 'generating' tras la 2a llamada: el polling
    // deberia haberse detenido, asi que no debe haber una 3a llamada.
    vi.advanceTimersByTime(3000);
    vi.advanceTimersByTime(3000);
    expect(listPending).toHaveBeenCalledTimes(2);
  });

  it('el polling no arranca si ninguna generacion esta generando', () => {
    vi.useFakeTimers();
    const listPending = vi.fn().mockReturnValue(of([READY]));

    createComponent({ listPending });
    vi.advanceTimersByTime(9000);

    expect(listPending).toHaveBeenCalledTimes(1);
  });

  it('onFilterTypeChange y onSearchTextChange llaman a listSaved con los filtros', () => {
    const listSaved = vi.fn().mockReturnValue(of([]));
    const fixture = createComponent({ listSaved });
    const component = fixture.componentInstance;
    listSaved.mockClear();

    component.onFilterTypeChange('knowledge');
    expect(listSaved).toHaveBeenCalledWith({ type: 'knowledge', q: undefined });

    component.onSearchTextChange('rebase');
    expect(listSaved).toHaveBeenCalledWith({ type: 'knowledge', q: 'rebase' });
  });

  it('generar() navega a /ejercicios/generar', () => {
    const fixture = createComponent({});
    const router = TestBed.inject(Router);
    const navigateSpy = vi.spyOn(router, 'navigate');

    fixture.componentInstance.generar();
    expect(navigateSpy).toHaveBeenCalledWith(['/ejercicios/generar']);
  });

  it('revisar(generation) navega a /ejercicios/{id}/revisar', () => {
    const fixture = createComponent({});
    const router = TestBed.inject(Router);
    const navigateSpy = vi.spyOn(router, 'navigate');

    fixture.componentInstance.revisar(READY);
    expect(navigateSpy).toHaveBeenCalledWith(['/ejercicios', READY.id, 'revisar']);
  });

  it('eliminar() pide confirmacion: si se confirma, llama a delete y refresca la lista', () => {
    let listSavedCalls = 0;
    const listSaved = vi.fn(() => {
      listSavedCalls += 1;
      return of(listSavedCalls === 1 ? [SAVED_ITEM] : []);
    });
    const deleteFn = vi.fn().mockReturnValue(of(SAVED_ITEM));

    const fixture = createComponent({ listSaved, deleteFn });
    const component = fixture.componentInstance;
    vi.spyOn(component, 'confirmarEliminar').mockReturnValue(true);

    component.eliminar(SAVED_ITEM);

    expect(deleteFn).toHaveBeenCalledWith(SAVED_ITEM.id);
    expect(listSavedCalls).toBe(2);
    expect(component.saved()).toEqual([]);
  });

  it('eliminar() no llama a delete si no se confirma', () => {
    const deleteFn = vi.fn().mockReturnValue(of(SAVED_ITEM));
    const fixture = createComponent({ deleteFn });
    const component = fixture.componentInstance;
    vi.spyOn(component, 'confirmarEliminar').mockReturnValue(false);

    component.eliminar(SAVED_ITEM);

    expect(deleteFn).not.toHaveBeenCalled();
  });
});

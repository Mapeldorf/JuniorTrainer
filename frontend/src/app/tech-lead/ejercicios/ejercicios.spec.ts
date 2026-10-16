import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { of } from 'rxjs';
import { GenerationsApiService } from '../../core/generations-api.service';
import { GenerationTrackerService } from '../../core/generation-tracker.service';
import {
  GenerationDetail,
  GenerationStatus,
  GenerationSummary,
  SavedExerciseListItem,
} from '../../core/generations-api.model';
import { SupabaseService } from '../../core/supabase.service';
import { EjerciciosComponent } from './ejercicios';

const GENERATING: GenerationSummary = {
  id: 'g1',
  status: 'generating',
  technologies: ['Git'],
  repo: null,
  kind: 'knowledge',
  error_message: null,
  created_at: '2026-01-01',
};

const READY: GenerationSummary = { ...GENERATING, status: 'ready', technologies: ['Git', 'Python'] };

const ERROR: GenerationSummary = {
  ...GENERATING,
  status: 'error',
  technologies: ['Rust'],
  error_message: 'fallo de prueba',
};

const SAVED_ITEM: SavedExerciseListItem = {
  id: 'e1',
  type: 'knowledge',
  name: 'Rebase en Git',
  statement: 'Explica que hace git rebase',
  code: [],
  expected_answer: 'respuesta esperada',
  technologies: ['Git'],
  repo: null,
  block_usage_count: 0,
};

function detail(
  id: string,
  status: GenerationStatus,
  errorMessage: string | null = null,
): GenerationDetail {
  return { id, status, error_message: errorMessage, candidates: [] };
}

describe('EjerciciosComponent', () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  function makeTracker(trackedIds: string[] = []) {
    let ids = [...trackedIds];
    return {
      add: vi.fn((id: string) => {
        if (!ids.includes(id)) {
          ids = [...ids, id];
        }
      }),
      list: vi.fn(() => [...ids]),
      remove: vi.fn((id: string) => {
        ids = ids.filter((x) => x !== id);
      }),
    };
  }

  function createComponent(opts: {
    listPending?: ReturnType<typeof vi.fn>;
    listSaved?: ReturnType<typeof vi.fn>;
    deleteFn?: ReturnType<typeof vi.fn>;
    getDetail?: ReturnType<typeof vi.fn>;
    tracker?: ReturnType<typeof makeTracker>;
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
            getDetail: opts.getDetail ?? vi.fn().mockReturnValue(of(detail('g1', 'generating'))),
          },
        },
        { provide: GenerationTrackerService, useValue: opts.tracker ?? makeTracker() },
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
    expect(text).toContain(SAVED_ITEM.name);
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

  it('eliminar() pide confirmacion: si se confirma, llama a delete y refresca la lista', async () => {
    let listSavedCalls = 0;
    const listSaved = vi.fn(() => {
      listSavedCalls += 1;
      return of(listSavedCalls === 1 ? [SAVED_ITEM] : []);
    });
    const deleteFn = vi.fn().mockReturnValue(of(SAVED_ITEM));

    const fixture = createComponent({ listSaved, deleteFn });
    const component = fixture.componentInstance;
    vi.spyOn(component, 'confirmarEliminar').mockResolvedValue(true);

    await component.eliminar(SAVED_ITEM);

    expect(deleteFn).toHaveBeenCalledWith(SAVED_ITEM.id);
    expect(listSavedCalls).toBe(2);
    expect(component.saved()).toEqual([]);
  });

  it('eliminar() no llama a delete si no se confirma', async () => {
    const deleteFn = vi.fn().mockReturnValue(of(SAVED_ITEM));
    const fixture = createComponent({ deleteFn });
    const component = fixture.componentInstance;
    vi.spyOn(component, 'confirmarEliminar').mockResolvedValue(false);

    await component.eliminar(SAVED_ITEM);

    expect(deleteFn).not.toHaveBeenCalled();
  });

  it('una generacion en error no se renderiza en la lista de pendientes', () => {
    const listPending = vi.fn().mockReturnValue(of([ERROR]));
    const fixture = createComponent({ listPending });
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';

    expect(fixture.componentInstance.pending()).toEqual([]);
    expect(text).not.toContain('Rust');
    expect(text).not.toContain('Error');
    expect(text).toContain('No hay ninguna generación pendiente');
  });

  it('una generacion rastreada que pasa a error produce el aviso y deja de rastrearse', () => {
    const tracker = makeTracker(['g1']);
    const getDetail = vi.fn().mockReturnValue(of(detail('g1', 'error', 'fallo')));
    const fixture = createComponent({ tracker, getDetail });

    expect(tracker.remove).toHaveBeenCalledWith('g1');
    expect(fixture.componentInstance.generationFailures()).toBe(1);
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('1 generación ha fallado');
  });

  it('dos generaciones rastreadas que pasan a error producen el aviso en plural', () => {
    const tracker = makeTracker(['g1', 'g2']);
    const getDetail = vi.fn((id: string) => of(detail(id, 'error')));
    const fixture = createComponent({ tracker, getDetail });

    expect(fixture.componentInstance.generationFailures()).toBe(2);
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('2 generaciones han fallado');
  });

  it('una generacion rastreada que queda ready deja de rastrearse sin aviso', () => {
    const tracker = makeTracker(['g1']);
    const getDetail = vi.fn().mockReturnValue(of(detail('g1', 'ready')));
    const fixture = createComponent({ tracker, getDetail });

    expect(tracker.remove).toHaveBeenCalledWith('g1');
    expect(fixture.componentInstance.generationFailures()).toBe(0);
  });

  it('el aviso de fallo se muestra como alert y se descarta con el boton', () => {
    const tracker = makeTracker(['g1']);
    const getDetail = vi.fn().mockReturnValue(of(detail('g1', 'error')));
    const fixture = createComponent({ tracker, getDetail });
    const el = fixture.nativeElement as HTMLElement;

    const alert = el.querySelector('[role="alert"]');
    expect(alert?.textContent).toContain('1 generación ha fallado');

    fixture.componentInstance.dismissGenerationFailures();
    fixture.detectChanges();

    expect(fixture.componentInstance.generationFailureNotice()).toBeNull();
    expect((fixture.nativeElement as HTMLElement).textContent ?? '').not.toContain('ha fallado');
  });
});

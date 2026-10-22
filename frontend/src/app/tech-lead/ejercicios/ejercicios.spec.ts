import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { of, Subject, throwError } from 'rxjs';
import { GenerationsApiService } from '../../core/generations-api.service';
import { GenerationTrackerService } from '../../core/generation-tracker.service';
import {
  GenerationDetail,
  GenerationStatus,
  GenerationSummary,
  SavedExerciseListItem,
  SavedExercisesPage,
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

function pageResponse(
  items: SavedExerciseListItem[],
  total = items.length,
  page = 1,
  pageSize = 10,
): SavedExercisesPage {
  return { items, total, page, page_size: pageSize };
}

function savedItem(id: string): SavedExerciseListItem {
  return { ...SAVED_ITEM, id };
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
    waitForPendingChange?: ReturnType<typeof vi.fn>;
    listSaved?: ReturnType<typeof vi.fn>;
    deleteFn?: ReturnType<typeof vi.fn>;
    deleteGenerationFn?: ReturnType<typeof vi.fn>;
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
            // Propuesta `long-polling-generaciones-pendientes`: sustituye al
            // sondeo cada 3s. Por defecto no emite nunca (como una espera
            // larga real que todavia no ha cambiado ni agotado su timeout):
            // un `of(...)` que resuelve al instante sobreescribiria el
            // listado de forma sincrona con datos que no reflejarian ya el
            // ultimo estado conocido, algo que una peticion HTTP real nunca
            // hace. Solo los tests que ejercitan el bucle la sobreescriben.
            waitForPendingChange: opts.waitForPendingChange ?? vi.fn().mockReturnValue(new Subject()),
            listSaved: opts.listSaved ?? vi.fn().mockReturnValue(of(pageResponse([]))),
            delete: opts.deleteFn ?? vi.fn().mockReturnValue(of(SAVED_ITEM)),
            deleteGeneration:
              opts.deleteGenerationFn ?? vi.fn().mockReturnValue(of(undefined)),
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
      listSaved: vi.fn().mockReturnValue(of(pageResponse([SAVED_ITEM]))),
    });
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Git, Python');
    expect(text).toContain('Por revisar');
    expect(text).toContain(SAVED_ITEM.name);
  });

  it('muestra el control de paginacion cuando hay mas de una pagina', () => {
    const items = Array.from({ length: 10 }, (_, i) => savedItem(`e${i}`));
    const listSaved = vi.fn().mockReturnValue(of(pageResponse(items, 11)));
    const fixture = createComponent({ listSaved });
    fixture.detectChanges();

    const el = fixture.nativeElement as HTMLElement;
    expect(el.querySelector('app-pagination')).not.toBeNull();
    expect(el.querySelector('nav[aria-label="Paginación"]')).not.toBeNull();
  });

  it('al cambiar de pagina mantiene la tabla montada, sin el placeholder que colapsa el scroll', () => {
    const subject = new Subject<SavedExercisesPage>();
    const listSaved = vi.fn().mockReturnValue(subject.asObservable());
    const fixture = createComponent({ listSaved });
    const component = fixture.componentInstance;

    const items = Array.from({ length: 10 }, (_, i) => savedItem(`e${i}`));
    subject.next(pageResponse(items, 30, 1, 10));
    fixture.detectChanges();
    expect(component.loadingSaved()).toBe(false);

    component.onPageChange(2);
    fixture.detectChanges();

    const el = fixture.nativeElement as HTMLElement;
    expect(component.refreshingSaved()).toBe(true);
    expect(el.querySelector('table')).not.toBeNull();
    expect(el.textContent).not.toContain('Cargando');
  });

  it('no muestra el control de paginacion con una sola pagina', () => {
    const items = Array.from({ length: 10 }, (_, i) => savedItem(`e${i}`));
    const listSaved = vi.fn().mockReturnValue(of(pageResponse(items, 10)));
    const fixture = createComponent({ listSaved });
    fixture.detectChanges();

    const el = fixture.nativeElement as HTMLElement;
    expect(el.querySelector('app-pagination')).toBeNull();
  });

  it('sin generaciones pendientes ni guardados, muestra los mensajes vacios', () => {
    const fixture = createComponent({});
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('No hay ninguna generación pendiente');
    expect(text).toContain('No hay ningún ejercicio guardado todavía');
  });

  it('tras la primera carga, si hay una generacion generando, encadena una espera larga sin esperar un temporizador', () => {
    const listPending = vi.fn().mockReturnValue(of([GENERATING]));
    const waitForPendingChange = vi.fn().mockReturnValue(of([READY]));

    createComponent({ listPending, waitForPendingChange });

    expect(waitForPendingChange).toHaveBeenCalledTimes(1);
  });

  it('sigue encadenando la espera larga mientras la respuesta siga teniendo una generacion generando', () => {
    const listPending = vi.fn().mockReturnValue(of([GENERATING]));
    let calls = 0;
    const waitForPendingChange = vi.fn(() => {
      calls += 1;
      return of(calls < 3 ? [GENERATING] : [READY]);
    });

    createComponent({ listPending, waitForPendingChange });

    expect(waitForPendingChange).toHaveBeenCalledTimes(3);
  });

  it('la espera larga no arranca si la primera carga no tiene ninguna generacion generando', () => {
    const listPending = vi.fn().mockReturnValue(of([READY]));
    const waitForPendingChange = vi.fn().mockReturnValue(of([READY]));

    createComponent({ listPending, waitForPendingChange });

    expect(waitForPendingChange).not.toHaveBeenCalled();
  });

  it('un fallo en la espera larga no detiene el bucle: se reintenta', () => {
    const listPending = vi.fn().mockReturnValue(of([GENERATING]));
    let calls = 0;
    const waitForPendingChange = vi.fn(() => {
      calls += 1;
      return calls === 1 ? throwError(() => new Error('fallo de red')) : of([READY]);
    });

    const fixture = createComponent({ listPending, waitForPendingChange });

    expect(waitForPendingChange).toHaveBeenCalledTimes(2);
    expect(fixture.componentInstance.error()).toBe(
      'No se han podido cargar las generaciones pendientes.',
    );
  });

  it('una generacion rastreada que sigue generating en la respuesta no genera una consulta a getDetail', () => {
    const tracker = makeTracker(['g1']);
    const listPending = vi.fn().mockReturnValue(of([GENERATING]));
    // Pasa a `ready` sin desaparecer del listado (sigue visible con el
    // mismo id): ni la primera carga ni la espera larga deberian
    // necesitar consultar getDetail para saberlo.
    const waitForPendingChange = vi.fn().mockReturnValue(of([READY]));
    const getDetail = vi.fn();

    createComponent({ listPending, waitForPendingChange, tracker, getDetail });

    expect(getDetail).not.toHaveBeenCalled();
  });

  it('una generacion rastreada que llega a ready sin desaparecer del listado deja de rastrearse y detiene el bucle', () => {
    // Regresion: si no se retira del rastreo al quedar visible-y-ready,
    // `hayRastreadas` se queda en true para siempre y la espera larga se
    // encadena sin fin (bug detectado al implementar esta tarea).
    const tracker = makeTracker(['g1']);
    const listPending = vi.fn().mockReturnValue(of([GENERATING]));
    const waitForPendingChange = vi.fn().mockReturnValue(of([READY]));

    createComponent({ listPending, waitForPendingChange, tracker });

    expect(tracker.remove).toHaveBeenCalledWith('g1');
    expect(waitForPendingChange).toHaveBeenCalledTimes(1);
  });

  it('una generacion rastreada que desaparece del listado sigue generando una consulta a getDetail', () => {
    const tracker = makeTracker(['g1']);
    const listPending = vi.fn().mockReturnValue(of([]));
    const getDetail = vi.fn().mockReturnValue(of(detail('g1', 'error')));

    createComponent({ listPending, tracker, getDetail });

    expect(getDetail).toHaveBeenCalledWith('g1');
  });

  it('la primera carga pide la pagina 1 con 10 por pagina', () => {
    const listSaved = vi.fn().mockReturnValue(of(pageResponse([])));
    createComponent({ listSaved });

    expect(listSaved).toHaveBeenCalledWith({
      type: undefined,
      q: undefined,
      page: 1,
      page_size: 10,
    });
  });

  it('onFilterTypeChange llama a listSaved desde la pagina 1 con los filtros', () => {
    const listSaved = vi.fn().mockReturnValue(of(pageResponse([])));
    const fixture = createComponent({ listSaved });
    const component = fixture.componentInstance;
    listSaved.mockClear();

    component.onFilterTypeChange('knowledge');
    expect(listSaved).toHaveBeenCalledWith({
      type: 'knowledge',
      q: undefined,
      page: 1,
      page_size: 10,
    });
  });

  it('onSearchTextChange solo actualiza el texto, sin llamar a listSaved', () => {
    const listSaved = vi.fn().mockReturnValue(of(pageResponse([])));
    const fixture = createComponent({ listSaved });
    const component = fixture.componentInstance;
    listSaved.mockClear();

    component.onSearchTextChange('rebase');
    expect(listSaved).not.toHaveBeenCalled();
  });

  it('buscarPorTexto llama a listSaved desde la pagina 1 con el texto escrito', () => {
    const listSaved = vi.fn().mockReturnValue(of(pageResponse([])));
    const fixture = createComponent({ listSaved });
    const component = fixture.componentInstance;
    component.onFilterTypeChange('knowledge');
    listSaved.mockClear();

    component.onSearchTextChange('rebase');
    component.buscarPorTexto();
    expect(listSaved).toHaveBeenCalledWith({
      type: 'knowledge',
      q: 'rebase',
      page: 1,
      page_size: 10,
    });
  });

  it('onFilterTypeChange vuelve a la pagina 1 aunque estuviera en otra', () => {
    const listSaved = vi.fn().mockReturnValue(of(pageResponse([SAVED_ITEM], 30)));
    const fixture = createComponent({ listSaved });
    const component = fixture.componentInstance;

    component.onPageChange(3);
    expect(component.page()).toBe(3);

    listSaved.mockClear();
    component.onFilterTypeChange('debug');
    expect(component.page()).toBe(1);
    expect(listSaved).toHaveBeenCalledWith(
      expect.objectContaining({ page: 1, page_size: 10 }),
    );
  });

  it('onPageChange carga la pagina indicada', () => {
    const listSaved = vi.fn().mockReturnValue(of(pageResponse([SAVED_ITEM], 30)));
    const fixture = createComponent({ listSaved });
    const component = fixture.componentInstance;
    listSaved.mockClear();

    component.onPageChange(2);

    expect(component.page()).toBe(2);
    expect(listSaved).toHaveBeenCalledWith(expect.objectContaining({ page: 2, page_size: 10 }));
  });

  it('onPageChange ignora la pagina actual y las fuera de rango', () => {
    const listSaved = vi.fn().mockReturnValue(of(pageResponse([SAVED_ITEM], 30)));
    const fixture = createComponent({ listSaved });
    const component = fixture.componentInstance;
    listSaved.mockClear();

    component.onPageChange(1);
    component.onPageChange(99);
    component.onPageChange(0);

    expect(listSaved).not.toHaveBeenCalled();
    expect(component.page()).toBe(1);
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

  it('el boton Eliminar solo aparece en las generaciones ready', () => {
    const listPending = vi.fn().mockReturnValue(of([READY, { ...GENERATING, id: 'g2' }]));
    const fixture = createComponent({ listPending });
    const el = fixture.nativeElement as HTMLElement;

    const eliminarButtons = Array.from(el.querySelectorAll('button')).filter(
      (b) => b.textContent?.trim() === 'Eliminar',
    );
    expect(eliminarButtons.length).toBe(1);
  });

  it('una generacion generating no muestra el boton Eliminar', () => {
    const listPending = vi.fn().mockReturnValue(of([GENERATING]));
    const fixture = createComponent({ listPending });
    const el = fixture.nativeElement as HTMLElement;

    const eliminarButtons = Array.from(el.querySelectorAll('button')).filter(
      (b) => b.textContent?.trim() === 'Eliminar',
    );
    expect(eliminarButtons.length).toBe(0);
  });

  it('eliminarGeneracion() pide confirmacion: si se confirma, llama a deleteGeneration y recarga pendientes', async () => {
    let listPendingCalls = 0;
    const listPending = vi.fn(() => {
      listPendingCalls += 1;
      return of(listPendingCalls === 1 ? [READY] : []);
    });
    const deleteGenerationFn = vi.fn().mockReturnValue(of(undefined));

    const fixture = createComponent({ listPending, deleteGenerationFn });
    const component = fixture.componentInstance;
    vi.spyOn(component, 'confirmarEliminarGeneracion').mockResolvedValue(true);

    await component.eliminarGeneracion(READY);

    expect(deleteGenerationFn).toHaveBeenCalledWith(READY.id);
    expect(listPendingCalls).toBe(2);
  });

  it('eliminarGeneracion() no llama a deleteGeneration si no se confirma', async () => {
    const deleteGenerationFn = vi.fn().mockReturnValue(of(undefined));
    const fixture = createComponent({ deleteGenerationFn });
    const component = fixture.componentInstance;
    vi.spyOn(component, 'confirmarEliminarGeneracion').mockResolvedValue(false);

    await component.eliminarGeneracion(READY);

    expect(deleteGenerationFn).not.toHaveBeenCalled();
  });

  it('eliminarGeneracion() muestra el error de la pantalla si la peticion falla', async () => {
    const deleteGenerationFn = vi.fn().mockReturnValue(throwError(() => new Error('fallo')));
    const fixture = createComponent({ deleteGenerationFn });
    const component = fixture.componentInstance;
    vi.spyOn(component, 'confirmarEliminarGeneracion').mockResolvedValue(true);

    await component.eliminarGeneracion(READY);

    expect(component.error()).toBe('No se ha podido eliminar la generación.');
  });

  it('pulsar Ver abre el detalle con el ejercicio correcto', () => {
    const listSaved = vi.fn().mockReturnValue(of(pageResponse([SAVED_ITEM])));
    const fixture = createComponent({ listSaved });
    const el = fixture.nativeElement as HTMLElement;

    const verButton = Array.from(el.querySelectorAll('button')).find(
      (b) => b.textContent?.trim() === 'Ver',
    );
    expect(verButton).toBeDefined();
    verButton!.click();
    fixture.detectChanges();

    const dialog = el.querySelector('[role="dialog"]');
    expect(dialog).not.toBeNull();
    expect(dialog?.textContent).toContain(SAVED_ITEM.statement);
    expect(dialog?.textContent).toContain(SAVED_ITEM.expected_answer!);
  });

  it('cerrar el detalle vuelve al listado sin modificar el ejercicio', () => {
    const listSaved = vi.fn().mockReturnValue(of(pageResponse([SAVED_ITEM])));
    const fixture = createComponent({ listSaved });
    const component = fixture.componentInstance;
    const el = fixture.nativeElement as HTMLElement;

    component.ver(SAVED_ITEM);
    fixture.detectChanges();
    expect(el.querySelector('[role="dialog"]')).not.toBeNull();

    component.cerrarDetalle();
    fixture.detectChanges();

    expect(el.querySelector('[role="dialog"]')).toBeNull();
    expect(component.saved()).toEqual([SAVED_ITEM]);
  });

  it('eliminar() pide confirmacion: si se confirma, llama a delete y refresca la lista', async () => {
    let listSavedCalls = 0;
    const listSaved = vi.fn(() => {
      listSavedCalls += 1;
      return of(listSavedCalls === 1 ? pageResponse([SAVED_ITEM]) : pageResponse([]));
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

  it('eliminar() el unico ejercicio de una pagina posterior retrocede de pagina', async () => {
    const listSaved = vi
      .fn()
      .mockReturnValue(of(pageResponse([savedItem('e2')], 11, 2, 10)));
    const deleteFn = vi.fn().mockReturnValue(of(SAVED_ITEM));

    const fixture = createComponent({ listSaved, deleteFn });
    const component = fixture.componentInstance;
    component.page.set(2);
    vi.spyOn(component, 'confirmarEliminar').mockResolvedValue(true);

    await component.eliminar(savedItem('e2'));

    expect(component.page()).toBe(1);
  });

  it('eliminar() en la primera pagina no retrocede', async () => {
    const listSaved = vi.fn().mockReturnValue(of(pageResponse([SAVED_ITEM])));
    const deleteFn = vi.fn().mockReturnValue(of(SAVED_ITEM));

    const fixture = createComponent({ listSaved, deleteFn });
    const component = fixture.componentInstance;
    vi.spyOn(component, 'confirmarEliminar').mockResolvedValue(true);

    await component.eliminar(SAVED_ITEM);

    expect(component.page()).toBe(1);
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

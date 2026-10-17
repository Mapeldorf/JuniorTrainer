import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { environment } from '../../environments/environment';
import { GenerationsApiService } from './generations-api.service';
import {
  GenerationDetail,
  GenerationSummary,
  SavedExercise,
  SavedExercisesPage,
  StartGenerationResponse,
  Technology,
} from './generations-api.model';

describe('GenerationsApiService', () => {
  let service: GenerationsApiService;
  let httpTesting: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(GenerationsApiService);
    httpTesting = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTesting.verify();
  });

  it('listPending() llama a GET /generations', () => {
    const expected: GenerationSummary[] = [
      {
        id: 'g1',
        status: 'ready',
        technologies: ['Git'],
        repo: null,
        kind: 'knowledge',
        error_message: null,
        created_at: '2026-01-01',
      },
    ];

    let result: GenerationSummary[] | undefined;
    service.listPending().subscribe((r) => (result = r));

    const req = httpTesting.expectOne(`${environment.apiUrl}/generations`);
    expect(req.request.method).toBe('GET');
    req.flush(expected);

    expect(result).toEqual(expected);
  });

  it('start(...) llama a POST /generations con el body', () => {
    const expected: StartGenerationResponse = { id: 'g1' };

    let result: StartGenerationResponse | undefined;
    service
      .start({ technologies: ['Git'], owner: null, repo: null, kind: 'knowledge', count: 3 })
      .subscribe((r) => (result = r));

    const req = httpTesting.expectOne(`${environment.apiUrl}/generations`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({
      technologies: ['Git'],
      owner: null,
      repo: null,
      kind: 'knowledge',
      count: 3,
    });
    req.flush(expected);

    expect(result).toEqual(expected);
  });

  it('getTechnologies() llama a GET /technologies', () => {
    const expected: Technology[] = [
      { id: 't1', name: 'Angular' },
      { id: 't2', name: 'RxJS' },
    ];

    let result: Technology[] | undefined;
    service.getTechnologies().subscribe((r) => (result = r));

    const req = httpTesting.expectOne(`${environment.apiUrl}/technologies`);
    expect(req.request.method).toBe('GET');
    req.flush(expected);

    expect(result).toEqual(expected);
  });

  it('getDetail(id) llama a GET /generations/{id}', () => {
    const expected: GenerationDetail = {
      id: 'g1',
      status: 'ready',
      error_message: null,
      candidates: [],
    };

    let result: GenerationDetail | undefined;
    service.getDetail('g1').subscribe((r) => (result = r));

    const req = httpTesting.expectOne(`${environment.apiUrl}/generations/g1`);
    expect(req.request.method).toBe('GET');
    req.flush(expected);

    expect(result).toEqual(expected);
  });

  it('close(id) llama a POST /generations/{id}/close', () => {
    const expected: GenerationSummary = {
      id: 'g1',
      status: 'done',
      technologies: ['Git'],
      repo: null,
      kind: 'knowledge',
      error_message: null,
      created_at: '2026-01-01',
    };

    let result: GenerationSummary | undefined;
    service.close('g1').subscribe((r) => (result = r));

    const req = httpTesting.expectOne(`${environment.apiUrl}/generations/g1/close`);
    expect(req.request.method).toBe('POST');
    req.flush(expected);

    expect(result).toEqual(expected);
  });

  it('deleteGeneration(id) llama a DELETE /generations/{id}', () => {
    let called = false;
    service.deleteGeneration('g1').subscribe(() => (called = true));

    const req = httpTesting.expectOne(`${environment.apiUrl}/generations/g1`);
    expect(req.request.method).toBe('DELETE');
    req.flush(null);

    expect(called).toBe(true);
  });

  it('listSaved(filters) llama a GET /exercises con los parametros de filtro y paginacion', () => {
    const expected: SavedExercisesPage = { items: [], total: 0, page: 2, page_size: 10 };

    let result: SavedExercisesPage | undefined;
    service
      .listSaved({ type: 'knowledge', q: 'texto', page: 2, page_size: 10 })
      .subscribe((r) => (result = r));

    const req = httpTesting.expectOne(
      (r) => r.url === `${environment.apiUrl}/exercises` && r.method === 'GET',
    );
    expect(req.request.params.get('type')).toBe('knowledge');
    expect(req.request.params.get('q')).toBe('texto');
    expect(req.request.params.get('page')).toBe('2');
    expect(req.request.params.get('page_size')).toBe('10');
    req.flush(expected);

    expect(result).toEqual(expected);
  });

  it('listSaved() sin filtros llama a GET /exercises sin parametros', () => {
    let result: SavedExercisesPage | undefined;
    service.listSaved().subscribe((r) => (result = r));

    const req = httpTesting.expectOne(`${environment.apiUrl}/exercises`);
    expect(req.request.method).toBe('GET');
    expect(req.request.params.keys().length).toBe(0);
    const expected: SavedExercisesPage = { items: [], total: 0, page: 1, page_size: 0 };
    req.flush(expected);

    expect(result).toEqual(expected);
  });

  it('save(exerciseId) sin respuesta editada llama a POST /exercises/{id}/save con body vacio', () => {
    const expected: SavedExercise = {
      id: 'e1',
      type: 'knowledge',
      name: 'nombre',
      statement: 'enunciado',
      code: [],
      expected_answer: 'original',
    };

    let result: SavedExercise | undefined;
    service.save('e1').subscribe((r) => (result = r));

    const req = httpTesting.expectOne(`${environment.apiUrl}/exercises/e1/save`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({});
    req.flush(expected);

    expect(result).toEqual(expected);
  });

  it('save(exerciseId, { expected_answer }) llama a POST /exercises/{id}/save con expected_answer', () => {
    const expected: SavedExercise = {
      id: 'e1',
      type: 'knowledge',
      name: 'nombre',
      statement: 'enunciado',
      code: [],
      expected_answer: 'editada',
    };

    let result: SavedExercise | undefined;
    service.save('e1', { expected_answer: 'editada' }).subscribe((r) => (result = r));

    const req = httpTesting.expectOne(`${environment.apiUrl}/exercises/e1/save`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ expected_answer: 'editada' });
    req.flush(expected);

    expect(result).toEqual(expected);
  });

  it('save(exerciseId, { name }) llama a POST /exercises/{id}/save con name', () => {
    const expected: SavedExercise = {
      id: 'e1',
      type: 'knowledge',
      name: 'nombre editado',
      statement: 'enunciado',
      code: [],
      expected_answer: 'original',
    };

    let result: SavedExercise | undefined;
    service.save('e1', { name: 'nombre editado' }).subscribe((r) => (result = r));

    const req = httpTesting.expectOne(`${environment.apiUrl}/exercises/e1/save`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ name: 'nombre editado' });
    req.flush(expected);

    expect(result).toEqual(expected);
  });

  it('delete(exerciseId) llama a PATCH /exercises/{id} con deleted: true', () => {
    const expected: SavedExercise = {
      id: 'e1',
      type: 'knowledge',
      name: 'nombre',
      statement: 'enunciado',
      code: [],
      expected_answer: null,
    };

    let result: SavedExercise | undefined;
    service.delete('e1').subscribe((r) => (result = r));

    const req = httpTesting.expectOne(`${environment.apiUrl}/exercises/e1`);
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual({ deleted: true });
    req.flush(expected);

    expect(result).toEqual(expected);
  });
});

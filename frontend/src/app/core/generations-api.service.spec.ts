import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { environment } from '../../environments/environment';
import { GenerationsApiService } from './generations-api.service';
import {
  GenerationDetail,
  GenerationSummary,
  SavedExercise,
  SavedExerciseListItem,
  StartGenerationResponse,
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
        repo_path: null,
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
      .start({ technologies: ['Git'], repo_path: null, kind: 'knowledge', count: 3 })
      .subscribe((r) => (result = r));

    const req = httpTesting.expectOne(`${environment.apiUrl}/generations`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({
      technologies: ['Git'],
      repo_path: null,
      kind: 'knowledge',
      count: 3,
    });
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
      repo_path: null,
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

  it('listSaved(filters) llama a GET /exercises con los parametros de filtro', () => {
    const expected: SavedExerciseListItem[] = [];

    let result: SavedExerciseListItem[] | undefined;
    service.listSaved({ type: 'knowledge', q: 'texto' }).subscribe((r) => (result = r));

    const req = httpTesting.expectOne(
      (r) => r.url === `${environment.apiUrl}/exercises` && r.method === 'GET',
    );
    expect(req.request.params.get('type')).toBe('knowledge');
    expect(req.request.params.get('q')).toBe('texto');
    req.flush(expected);

    expect(result).toEqual(expected);
  });

  it('listSaved() sin filtros llama a GET /exercises sin parametros', () => {
    service.listSaved().subscribe();

    const req = httpTesting.expectOne(`${environment.apiUrl}/exercises`);
    expect(req.request.method).toBe('GET');
    expect(req.request.params.keys().length).toBe(0);
    req.flush([]);
  });

  it('save(exerciseId) sin respuesta editada llama a POST /exercises/{id}/save con body vacio', () => {
    const expected: SavedExercise = {
      id: 'e1',
      type: 'knowledge',
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

  it('save(exerciseId, respuesta) llama a POST /exercises/{id}/save con expected_answer', () => {
    const expected: SavedExercise = {
      id: 'e1',
      type: 'knowledge',
      statement: 'enunciado',
      code: [],
      expected_answer: 'editada',
    };

    let result: SavedExercise | undefined;
    service.save('e1', 'editada').subscribe((r) => (result = r));

    const req = httpTesting.expectOne(`${environment.apiUrl}/exercises/e1/save`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ expected_answer: 'editada' });
    req.flush(expected);

    expect(result).toEqual(expected);
  });

  it('delete(exerciseId) llama a PATCH /exercises/{id} con deleted: true', () => {
    const expected: SavedExercise = {
      id: 'e1',
      type: 'knowledge',
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

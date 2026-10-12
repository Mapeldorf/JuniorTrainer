import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { environment } from '../../environments/environment';
import { AssignmentsApiService } from './assignments-api.service';
import { AssignmentDetail, AssignmentSummary, AnswerResult } from './assignments-api.model';

describe('AssignmentsApiService', () => {
  let service: AssignmentsApiService;
  let httpTesting: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(AssignmentsApiService);
    httpTesting = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTesting.verify();
  });

  it('listMine() llama a GET /assignments', () => {
    const expected: AssignmentSummary[] = [
      { id: 'a1', block_name: 'Bloque 1', assigned_at: '2026-01-01', answered_count: 0, total_count: 2 },
    ];

    let result: AssignmentSummary[] | undefined;
    service.listMine().subscribe((r) => (result = r));

    const req = httpTesting.expectOne(`${environment.apiUrl}/assignments`);
    expect(req.request.method).toBe('GET');
    req.flush(expected);

    expect(result).toEqual(expected);
  });

  it('getDetail(id) llama a GET /assignments/{id}', () => {
    const expected: AssignmentDetail = {
      id: 'a1',
      block_name: 'Bloque 1',
      assigned_at: '2026-01-01',
      exercises: [],
    };

    let result: AssignmentDetail | undefined;
    service.getDetail('a1').subscribe((r) => (result = r));

    const req = httpTesting.expectOne(`${environment.apiUrl}/assignments/a1`);
    expect(req.request.method).toBe('GET');
    req.flush(expected);

    expect(result).toEqual(expected);
  });

  it('submitAnswer(...) llama a POST /assignments/{id}/exercises/{id}/answer con el texto', () => {
    const expected: AnswerResult = {
      exercise_id: 'e1',
      verdict: 'correct',
      justification: 'bien',
      answered_at: '2026-01-01',
    };

    let result: AnswerResult | undefined;
    service.submitAnswer('a1', 'e1', 'mi respuesta').subscribe((r) => (result = r));

    const req = httpTesting.expectOne(`${environment.apiUrl}/assignments/a1/exercises/e1/answer`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ text: 'mi respuesta' });
    req.flush(expected);

    expect(result).toEqual(expected);
  });
});

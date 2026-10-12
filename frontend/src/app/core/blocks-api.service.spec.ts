import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { environment } from '../../environments/environment';
import { BlocksApiService } from './blocks-api.service';
import {
  AssignBlockResponse,
  BlockDetail,
  BlockSummary,
  StudentProgress,
} from './blocks-api.model';

describe('BlocksApiService', () => {
  let service: BlocksApiService;
  let httpTesting: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(BlocksApiService);
    httpTesting = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTesting.verify();
  });

  it('list() sin argumentos llama a GET /blocks?deleted=false', () => {
    const expected: BlockSummary[] = [];

    let result: BlockSummary[] | undefined;
    service.list().subscribe((r) => (result = r));

    const req = httpTesting.expectOne(
      (r) => r.url === `${environment.apiUrl}/blocks` && r.method === 'GET',
    );
    expect(req.request.params.get('deleted')).toBe('false');
    req.flush(expected);

    expect(result).toEqual(expected);
  });

  it('list(true) llama a GET /blocks?deleted=true', () => {
    service.list(true).subscribe();

    const req = httpTesting.expectOne(
      (r) => r.url === `${environment.apiUrl}/blocks` && r.method === 'GET',
    );
    expect(req.request.params.get('deleted')).toBe('true');
    req.flush([]);
  });

  it('create(body) llama a POST /blocks con el body', () => {
    const expected: BlockDetail = {
      id: 'b1',
      name: 'Bloque 1',
      created_at: '2026-01-01',
      updated_at: '2026-01-01',
      deleted_at: null,
      exercises: [],
      resolved: false,
    };

    let result: BlockDetail | undefined;
    service.create({ name: 'Bloque 1', exercise_ids: ['e1'] }).subscribe((r) => (result = r));

    const req = httpTesting.expectOne(`${environment.apiUrl}/blocks`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ name: 'Bloque 1', exercise_ids: ['e1'] });
    req.flush(expected);

    expect(result).toEqual(expected);
  });

  it('getDetail(id) llama a GET /blocks/{id}', () => {
    const expected: BlockDetail = {
      id: 'b1',
      name: 'Bloque 1',
      created_at: '2026-01-01',
      updated_at: '2026-01-01',
      deleted_at: null,
      exercises: [],
      resolved: false,
    };

    let result: BlockDetail | undefined;
    service.getDetail('b1').subscribe((r) => (result = r));

    const req = httpTesting.expectOne(`${environment.apiUrl}/blocks/b1`);
    expect(req.request.method).toBe('GET');
    req.flush(expected);

    expect(result).toEqual(expected);
  });

  it('update(id, body) llama a PATCH /blocks/{id} con el body', () => {
    service.update('b1', { name: 'Nuevo nombre' }).subscribe();

    const req = httpTesting.expectOne(`${environment.apiUrl}/blocks/b1`);
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual({ name: 'Nuevo nombre' });
    req.flush({});
  });

  it('delete(id) llama a DELETE /blocks/{id}', () => {
    service.delete('b1').subscribe();

    const req = httpTesting.expectOne(`${environment.apiUrl}/blocks/b1`);
    expect(req.request.method).toBe('DELETE');
    req.flush({});
  });

  it('assign(id, studentIds) llama a POST /blocks/{id}/assignments con student_ids', () => {
    const expected: AssignBlockResponse = {
      results: [{ student_id: 's1', status: 'created' }],
    };

    let result: AssignBlockResponse | undefined;
    service.assign('b1', ['s1']).subscribe((r) => (result = r));

    const req = httpTesting.expectOne(`${environment.apiUrl}/blocks/b1/assignments`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ student_ids: ['s1'] });
    req.flush(expected);

    expect(result).toEqual(expected);
  });

  it('getProgress(id) llama a GET /blocks/{id}/assignments', () => {
    const expected: StudentProgress[] = [];

    let result: StudentProgress[] | undefined;
    service.getProgress('b1').subscribe((r) => (result = r));

    const req = httpTesting.expectOne(`${environment.apiUrl}/blocks/b1/assignments`);
    expect(req.request.method).toBe('GET');
    req.flush(expected);

    expect(result).toEqual(expected);
  });
});

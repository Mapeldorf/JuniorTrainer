import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { environment } from '../../environments/environment';
import { UsersApiService } from './users-api.service';
import { InviteStudentResponse, StudentBlockAssignment, StudentSummary } from './users-api.model';

describe('UsersApiService', () => {
  let service: UsersApiService;
  let httpTesting: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(UsersApiService);
    httpTesting = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTesting.verify();
  });

  it('listStudents() llama a GET /users', () => {
    const expected: StudentSummary[] = [{ id: 's1', name: 'Ana', email: 'ana@example.com' }];

    let result: StudentSummary[] | undefined;
    service.listStudents().subscribe((r) => (result = r));

    const req = httpTesting.expectOne(`${environment.apiUrl}/users`);
    expect(req.request.method).toBe('GET');
    req.flush(expected);

    expect(result).toEqual(expected);
  });

  it('invite(body) llama a POST /users con el body', () => {
    const expected: InviteStudentResponse = { email: 'ana@example.com', status: 'invited' };

    let result: InviteStudentResponse | undefined;
    service
      .invite({ name: 'Ana', email: 'ana@example.com' })
      .subscribe((r) => (result = r));

    const req = httpTesting.expectOne(`${environment.apiUrl}/users`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ name: 'Ana', email: 'ana@example.com' });
    req.flush(expected);

    expect(result).toEqual(expected);
  });

  it('invite(body) con email duplicado propaga el 409 al subscriber sin envolverlo', () => {
    let nextCalled = false;
    let errorStatus: number | undefined;
    service.invite({ name: 'Ana', email: 'ana@example.com' }).subscribe({
      next: () => (nextCalled = true),
      error: (err) => (errorStatus = err.status),
    });

    const req = httpTesting.expectOne(`${environment.apiUrl}/users`);
    req.flush('ya existe', { status: 409, statusText: 'Conflict' });

    expect(nextCalled).toBe(false);
    expect(errorStatus).toBe(409);
  });

  it('getBlocks(studentId) llama a GET /users/{id}/blocks', () => {
    const expected: StudentBlockAssignment[] = [
      {
        assignment_id: 'a1',
        block_id: 'b1',
        block_name: 'Bloque 1',
        exercises: [],
      },
    ];

    let result: StudentBlockAssignment[] | undefined;
    service.getBlocks('s1').subscribe((r) => (result = r));

    const req = httpTesting.expectOne(`${environment.apiUrl}/users/s1/blocks`);
    expect(req.request.method).toBe('GET');
    req.flush(expected);

    expect(result).toEqual(expected);
  });
});

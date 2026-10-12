import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { environment } from '../../environments/environment';
import { authInterceptor } from './auth.interceptor';
import { SupabaseService } from './supabase.service';

/** El interceptor resuelve la sesion de forma asincrona (una `Promise`),
 * asi que la peticion real no llega a `HttpTestingController` hasta que
 * ese microtask se resuelve. Se espera un tick de macrotarea antes de
 * comprobarla (patron habitual para interceptores basados en Promise). */
function flushMicrotasks(): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, 0));
}

describe('authInterceptor', () => {
  let httpClient: HttpClient;
  let httpTesting: HttpTestingController;
  let getSessionSpy: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    getSessionSpy = vi.fn();

    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
        { provide: SupabaseService, useValue: { getSession: getSessionSpy } },
      ],
    });

    httpClient = TestBed.inject(HttpClient);
    httpTesting = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTesting.verify();
  });

  it('antepone el JWT a una peticion dirigida a la API', async () => {
    getSessionSpy.mockResolvedValue({ access_token: 'token-de-prueba' });

    httpClient.get(`${environment.apiUrl}/assignments`).subscribe();
    await flushMicrotasks();

    const req = httpTesting.expectOne(`${environment.apiUrl}/assignments`);
    expect(req.request.headers.get('Authorization')).toBe('Bearer token-de-prueba');
    req.flush([]);
  });

  it('no antepone nada a una peticion que no es de la API', async () => {
    getSessionSpy.mockResolvedValue({ access_token: 'token-de-prueba' });

    httpClient.get('https://otra-cosa.example.com/algo').subscribe();
    await flushMicrotasks();

    const req = httpTesting.expectOne('https://otra-cosa.example.com/algo');
    expect(req.request.headers.has('Authorization')).toBe(false);
    expect(getSessionSpy).not.toHaveBeenCalled();
    req.flush({});
  });

  it('no antepone nada si no hay sesion', async () => {
    getSessionSpy.mockResolvedValue(null);

    httpClient.get(`${environment.apiUrl}/assignments`).subscribe();
    await flushMicrotasks();

    const req = httpTesting.expectOne(`${environment.apiUrl}/assignments`);
    expect(req.request.headers.has('Authorization')).toBe(false);
    req.flush([]);
  });
});

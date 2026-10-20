import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
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
  let refreshSessionSpy: ReturnType<typeof vi.fn>;
  let signOutSpy: ReturnType<typeof vi.fn>;
  let navigateSpy: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    getSessionSpy = vi.fn();
    refreshSessionSpy = vi.fn();
    signOutSpy = vi.fn().mockResolvedValue(undefined);
    navigateSpy = vi.fn().mockResolvedValue(true);

    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
        {
          provide: SupabaseService,
          useValue: { getSession: getSessionSpy, refreshSession: refreshSessionSpy, signOut: signOutSpy },
        },
        { provide: Router, useValue: { navigate: navigateSpy } },
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

  it('reintenta una vez con el token renovado si el backend responde 401', async () => {
    getSessionSpy.mockResolvedValue({ access_token: 'token-caducado' });
    refreshSessionSpy.mockResolvedValue({ access_token: 'token-nuevo' });

    let result: unknown;
    httpClient.get(`${environment.apiUrl}/assignments`).subscribe((res) => (result = res));
    await flushMicrotasks();

    const firstReq = httpTesting.expectOne(`${environment.apiUrl}/assignments`);
    expect(firstReq.request.headers.get('Authorization')).toBe('Bearer token-caducado');
    firstReq.flush({ detail: 'Token invalido o caducado' }, { status: 401, statusText: 'Unauthorized' });
    await flushMicrotasks();

    expect(refreshSessionSpy).toHaveBeenCalled();
    const retryReq = httpTesting.expectOne(`${environment.apiUrl}/assignments`);
    expect(retryReq.request.headers.get('Authorization')).toBe('Bearer token-nuevo');
    retryReq.flush(['ok']);
    await flushMicrotasks();

    expect(result).toEqual(['ok']);
  });

  it('cierra sesion y manda a login si la renovacion tambien falla, propagando el 401', async () => {
    getSessionSpy.mockResolvedValue({ access_token: 'token-caducado' });
    refreshSessionSpy.mockResolvedValue(null);

    let error: unknown;
    httpClient.get(`${environment.apiUrl}/assignments`).subscribe({ error: (err) => (error = err) });
    await flushMicrotasks();

    const req = httpTesting.expectOne(`${environment.apiUrl}/assignments`);
    req.flush({ detail: 'Token invalido o caducado' }, { status: 401, statusText: 'Unauthorized' });
    await flushMicrotasks();

    expect(refreshSessionSpy).toHaveBeenCalled();
    expect(signOutSpy).toHaveBeenCalled();
    expect(navigateSpy).toHaveBeenCalledWith(['/login']);
    expect((error as { status: number }).status).toBe(401);
  });
});

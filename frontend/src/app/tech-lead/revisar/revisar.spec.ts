import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { of, throwError } from 'rxjs';
import { GenerationsApiService } from '../../core/generations-api.service';
import { GenerationDetail } from '../../core/generations-api.model';
import { SupabaseService } from '../../core/supabase.service';
import { RevisarComponent } from './revisar';

const READY_DETAIL: GenerationDetail = {
  id: 'g1',
  status: 'ready',
  error_message: null,
  candidates: [
    { id: 'c1', type: 'knowledge', statement: 'Pregunta 1', code: [], expected_answer: 'respuesta 1' },
    { id: 'c2', type: 'knowledge', statement: 'Pregunta 2', code: [], expected_answer: 'respuesta 2' },
  ],
};

describe('RevisarComponent', () => {
  function createComponent(opts: {
    getDetail: () => GenerationDetail;
    save?: ReturnType<typeof vi.fn>;
    close?: ReturnType<typeof vi.fn>;
    generationId?: string;
  }) {
    TestBed.configureTestingModule({
      imports: [RevisarComponent],
      providers: [
        provideRouter([]),
        { provide: SupabaseService, useValue: { signOut: async () => undefined } },
        {
          provide: GenerationsApiService,
          useValue: {
            getDetail: () => of(opts.getDetail()),
            save: opts.save ?? vi.fn().mockReturnValue(of({})),
            close: opts.close ?? vi.fn().mockReturnValue(of({})),
          },
        },
      ],
    });
    const fixture = TestBed.createComponent(RevisarComponent);
    fixture.componentRef.setInput('generationId', opts.generationId ?? 'g1');
    fixture.detectChanges();
    return fixture;
  }

  it('generacion en curso (generating): muestra el estado, no la lista de candidatos', () => {
    const fixture = createComponent({
      getDetail: () => ({ id: 'g1', status: 'generating', error_message: null, candidates: [] }),
    });
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('todavía está en curso');
    expect(fixture.nativeElement.querySelectorAll('input[type="checkbox"]').length).toBe(0);
  });

  it('generacion en error: muestra el mensaje de error, no la lista de candidatos', () => {
    const fixture = createComponent({
      getDetail: () => ({
        id: 'g1',
        status: 'error',
        error_message: 'el agente de codigo ha fallado',
        candidates: [],
      }),
    });
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('el agente de codigo ha fallado');
    expect(fixture.nativeElement.querySelectorAll('input[type="checkbox"]').length).toBe(0);
  });

  it('generacion lista (ready): muestra los candidatos con su respuesta esperada', () => {
    const fixture = createComponent({ getDetail: () => READY_DETAIL });
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Pregunta 1');
    expect(text).toContain('Pregunta 2');
    expect(fixture.nativeElement.querySelectorAll('input[type="checkbox"]').length).toBe(2);

    const component = fixture.componentInstance;
    expect(component.answerFor('c1')).toBe('respuesta 1');
    expect(component.answerFor('c2')).toBe('respuesta 2');
  });

  it('guardar() con 0 candidatos marcados: no llama a save(), pero si a close(), y navega', () => {
    const save = vi.fn().mockReturnValue(of({}));
    const close = vi.fn().mockReturnValue(of({}));
    const fixture = createComponent({ getDetail: () => READY_DETAIL, save, close });
    const router = TestBed.inject(Router);
    const navigateSpy = vi.spyOn(router, 'navigate');

    fixture.componentInstance.guardar();

    expect(save).not.toHaveBeenCalled();
    expect(close).toHaveBeenCalledWith('g1');
    expect(navigateSpy).toHaveBeenCalledWith(['/ejercicios']);
  });

  it('guardar() guarda solo los candidatos marcados, con su respuesta editada si cambio', () => {
    const save = vi.fn().mockReturnValue(of({}));
    const close = vi.fn().mockReturnValue(of({}));
    const fixture = createComponent({ getDetail: () => READY_DETAIL, save, close });
    const component = fixture.componentInstance;

    component.toggleSelected('c1');
    component.setAnswer('c1', 'respuesta 1 editada');
    // c2 no se marca: no deberia guardarse aunque se edite su respuesta
    component.setAnswer('c2', 'respuesta 2 editada, pero no marcada');

    component.guardar();

    expect(save).toHaveBeenCalledTimes(1);
    expect(save).toHaveBeenCalledWith('c1', 'respuesta 1 editada');
    expect(close).toHaveBeenCalledWith('g1');
  });

  it('guardar() omite expected_answer si no cambio respecto a la original', () => {
    const save = vi.fn().mockReturnValue(of({}));
    const fixture = createComponent({ getDetail: () => READY_DETAIL, save });
    const component = fixture.componentInstance;

    component.toggleSelected('c1');
    // no se llama a setAnswer: se guarda tal cual vino

    component.guardar();

    expect(save).toHaveBeenCalledWith('c1', undefined);
  });

  it('si close() falla, muestra un error y no navega', () => {
    const close = vi.fn().mockReturnValue(throwError(() => new Error('fallo')));
    const fixture = createComponent({ getDetail: () => READY_DETAIL, close });
    const component = fixture.componentInstance;
    const router = TestBed.inject(Router);
    const navigateSpy = vi.spyOn(router, 'navigate');

    component.guardar();

    expect(component.error()).not.toBeNull();
    expect(navigateSpy).not.toHaveBeenCalled();
  });

  it('cancelar() navega a /ejercicios', () => {
    const fixture = createComponent({ getDetail: () => READY_DETAIL });
    const router = TestBed.inject(Router);
    const navigateSpy = vi.spyOn(router, 'navigate');

    fixture.componentInstance.cancelar();
    expect(navigateSpy).toHaveBeenCalledWith(['/ejercicios']);
  });
});

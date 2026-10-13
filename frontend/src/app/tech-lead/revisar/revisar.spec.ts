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
    { id: 'c1', type: 'knowledge', name: 'Nombre 1', statement: 'Pregunta 1', code: [], expected_answer: 'respuesta 1' },
    { id: 'c2', type: 'knowledge', name: 'Nombre 2', statement: 'Pregunta 2', code: [], expected_answer: 'respuesta 2' },
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
    // 1 checkbox "Seleccionar todos" + 1 por candidato.
    expect(fixture.nativeElement.querySelectorAll('input[type="checkbox"]').length).toBe(3);

    const component = fixture.componentInstance;
    expect(component.answerFor('c1')).toBe('respuesta 1');
    expect(component.answerFor('c2')).toBe('respuesta 2');
  });

  // Tarea 1.1: preseleccion por defecto.
  it('al cargar, todos los candidatos salen premarcados sin haber hecho ningun click', () => {
    const fixture = createComponent({ getDetail: () => READY_DETAIL });
    const component = fixture.componentInstance;
    expect(component.isSelected('c1')).toBe(true);
    expect(component.isSelected('c2')).toBe(true);
  });

  // Tarea 2.1: allSelected() y toggleAll().
  it('allSelected() es true con todos marcados y false en cuanto se desmarca uno', () => {
    const fixture = createComponent({ getDetail: () => READY_DETAIL });
    const component = fixture.componentInstance;
    expect(component.allSelected()).toBe(true);

    component.toggleSelected('c1');
    expect(component.allSelected()).toBe(false);
  });

  it('toggleAll() marca todos si habia una seleccion parcial', () => {
    const fixture = createComponent({ getDetail: () => READY_DETAIL });
    const component = fixture.componentInstance;
    component.toggleSelected('c1'); // c1 queda desmarcado, c2 sigue marcado

    component.toggleAll();

    expect(component.isSelected('c1')).toBe(true);
    expect(component.isSelected('c2')).toBe(true);
    expect(component.allSelected()).toBe(true);
  });

  it('toggleAll() desmarca todos si ya estaba todo marcado', () => {
    const fixture = createComponent({ getDetail: () => READY_DETAIL });
    const component = fixture.componentInstance;

    component.toggleAll();

    expect(component.isSelected('c1')).toBe(false);
    expect(component.isSelected('c2')).toBe(false);
    expect(component.allSelected()).toBe(false);
  });

  // Tarea 2.2: checkbox "Seleccionar todos" en la plantilla.
  it('el checkbox "Seleccionar todos" existe y refleja allSelected()', () => {
    const fixture = createComponent({ getDetail: () => READY_DETAIL });
    const checkboxes = fixture.nativeElement.querySelectorAll('input[type="checkbox"]');
    const selectAllCheckbox = checkboxes[0] as HTMLInputElement;

    // Premarcado por defecto (tarea 1.1): el checkbox de "todos" arranca marcado.
    expect(selectAllCheckbox.checked).toBe(true);

    fixture.componentInstance.toggleSelected('c1');
    fixture.detectChanges();
    expect(selectAllCheckbox.checked).toBe(false);
  });

  // Tarea 3.1: confirmarPerdida().
  it('confirmarPerdida() envuelve confirm() y el mensaje nombra cuantos candidatos se pierden', () => {
    const fixture = createComponent({ getDetail: () => READY_DETAIL });
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);

    const result = fixture.componentInstance.confirmarPerdida(2);

    expect(result).toBe(true);
    expect(confirmSpy).toHaveBeenCalledTimes(1);
    expect(confirmSpy.mock.calls[0][0]).toContain('2');
  });

  // Tarea 3.2: guardar() con seleccion parcial, cancelando la confirmacion.
  it('guardar() con candidatos sin marcar: si se cancela la confirmacion, no guarda ni cierra', () => {
    const save = vi.fn().mockReturnValue(of({}));
    const close = vi.fn().mockReturnValue(of({}));
    const fixture = createComponent({ getDetail: () => READY_DETAIL, save, close });
    const component = fixture.componentInstance;
    const confirmSpy = vi.spyOn(component, 'confirmarPerdida').mockReturnValue(false);

    component.toggleSelected('c2'); // c2 queda sin marcar, c1 sigue marcado
    component.guardar();

    expect(confirmSpy).toHaveBeenCalledWith(1);
    expect(save).not.toHaveBeenCalled();
    expect(close).not.toHaveBeenCalled();
    expect(component.saving()).toBe(false);
    // La seleccion no cambia: sigue pudiendo seguir editando (requisito del change).
    expect(component.isSelected('c1')).toBe(true);
    expect(component.isSelected('c2')).toBe(false);
  });

  // Tarea 3.2: guardar() con seleccion parcial, confirmando la perdida.
  it('guardar() con candidatos sin marcar: si se confirma, guarda los marcados y cierra', () => {
    const save = vi.fn().mockReturnValue(of({}));
    const close = vi.fn().mockReturnValue(of({}));
    const fixture = createComponent({ getDetail: () => READY_DETAIL, save, close });
    const component = fixture.componentInstance;
    vi.spyOn(component, 'confirmarPerdida').mockReturnValue(true);

    component.toggleSelected('c2'); // c2 queda sin marcar, c1 sigue marcado
    component.guardar();

    expect(save).toHaveBeenCalledTimes(1);
    expect(save).toHaveBeenCalledWith('c1', { expected_answer: undefined, name: undefined });
    expect(close).toHaveBeenCalledWith('g1');
  });

  // Tarea 3.2: con todo marcado (el default) no se pide confirmacion.
  it('guardar() con todos los candidatos marcados: no pide confirmacion', () => {
    const save = vi.fn().mockReturnValue(of({}));
    const close = vi.fn().mockReturnValue(of({}));
    const fixture = createComponent({ getDetail: () => READY_DETAIL, save, close });
    const component = fixture.componentInstance;
    const confirmSpy = vi.spyOn(component, 'confirmarPerdida');

    component.guardar(); // nada desmarcado: queda tal cual la preseleccion

    expect(confirmSpy).not.toHaveBeenCalled();
    expect(save).toHaveBeenCalledTimes(2);
    expect(close).toHaveBeenCalledWith('g1');
  });

  it('guardar() con la respuesta editada de un candidato marcado', () => {
    const save = vi.fn().mockReturnValue(of({}));
    const close = vi.fn().mockReturnValue(of({}));
    const fixture = createComponent({ getDetail: () => READY_DETAIL, save, close });
    const component = fixture.componentInstance;

    component.toggleSelected('c2'); // deja solo c1 marcado (premarcado por defecto)
    component.setAnswer('c1', 'respuesta 1 editada');
    // c2 no esta marcado: no deberia guardarse aunque se edite su respuesta
    component.setAnswer('c2', 'respuesta 2 editada, pero no marcada');
    vi.spyOn(component, 'confirmarPerdida').mockReturnValue(true);

    component.guardar();

    expect(save).toHaveBeenCalledTimes(1);
    expect(save).toHaveBeenCalledWith('c1', { expected_answer: 'respuesta 1 editada', name: undefined });
    expect(close).toHaveBeenCalledWith('g1');
  });

  it('guardar() omite expected_answer y name si no cambiaron respecto a los originales', () => {
    const save = vi.fn().mockReturnValue(of({}));
    const fixture = createComponent({ getDetail: () => READY_DETAIL, save });
    const component = fixture.componentInstance;

    // Todo sigue marcado por defecto (tarea 1.1); no se edita nada.
    component.guardar();

    expect(save).toHaveBeenCalledWith('c1', { expected_answer: undefined, name: undefined });
    expect(save).toHaveBeenCalledWith('c2', { expected_answer: undefined, name: undefined });
  });

  it('guardar() guarda el nombre editado si cambio', () => {
    const save = vi.fn().mockReturnValue(of({}));
    const fixture = createComponent({ getDetail: () => READY_DETAIL, save });
    const component = fixture.componentInstance;

    component.setName('c1', 'Nombre 1 editado');
    component.guardar();

    expect(save).toHaveBeenCalledWith('c1', { expected_answer: undefined, name: 'Nombre 1 editado' });
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

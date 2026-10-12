import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { of, throwError } from 'rxjs';
import { AssignmentsApiService } from '../../core/assignments-api.service';
import { AssignmentDetail } from '../../core/assignments-api.model';
import { EjercicioComponent } from './ejercicio';

const BASE_DETAIL: AssignmentDetail = {
  id: 'a1',
  block_name: 'Bloque 1',
  assigned_at: '2026-01-01',
  exercises: [
    {
      exercise_id: 'e1',
      position: 1,
      statement: 'Enunciado 1',
      code: [],
      answered: true,
      answer_text: 'mi respuesta 1',
      verdict: 'correct',
      justification: 'Bien hecho',
    },
    {
      exercise_id: 'e2',
      position: 2,
      statement: 'Enunciado 2',
      code: [],
      answered: false,
      answer_text: null,
      verdict: null,
      justification: null,
    },
  ],
};

describe('EjercicioComponent', () => {
  function createComponent(opts: {
    getDetail: () => AssignmentDetail;
    assignmentId?: string;
    position?: string;
  }) {
    TestBed.configureTestingModule({
      imports: [EjercicioComponent],
      providers: [
        provideRouter([]),
        {
          provide: AssignmentsApiService,
          useValue: {
            getDetail: () => of(opts.getDetail()),
            submitAnswer: vi.fn(),
          },
        },
      ],
    });

    const fixture = TestBed.createComponent(EjercicioComponent);
    fixture.componentRef.setInput('assignmentId', opts.assignmentId ?? 'a1');
    fixture.componentRef.setInput('position', opts.position ?? '2');
    fixture.detectChanges();
    return fixture;
  }

  it('ejercicio sin responder (pantalla 9): no muestra verdict y permite escribir', () => {
    const fixture = createComponent({ getDetail: () => BASE_DETAIL, position: '2' });
    const component = fixture.componentInstance;

    expect(component.exercise()?.answered).toBe(false);
    expect(component.exercise()?.verdict).toBeNull();
  });

  it('ejercicio ya respondido (pantalla 10): expone su respuesta y su verdict', () => {
    const fixture = createComponent({ getDetail: () => BASE_DETAIL, position: '1' });
    const component = fixture.componentInstance;

    expect(component.exercise()?.answered).toBe(true);
    expect(component.verdictLabel(component.exercise()!.verdict)).toBe('Correcta');
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('mi respuesta 1');
    expect(text).toContain('Bien hecho');
  });

  it('Siguiente no pasa del ultimo ejercicio visible', () => {
    const fixture = createComponent({ getDetail: () => BASE_DETAIL, position: '2' });
    const component = fixture.componentInstance;
    const router = TestBed.inject(Router);
    const navigateSpy = vi.spyOn(router, 'navigate');

    component.siguiente();
    expect(navigateSpy).not.toHaveBeenCalled();
  });

  it('Anterior no pasa de la posicion 1', () => {
    const fixture = createComponent({ getDetail: () => BASE_DETAIL, position: '1' });
    const component = fixture.componentInstance;
    const router = TestBed.inject(Router);
    const navigateSpy = vi.spyOn(router, 'navigate');

    component.anterior();
    expect(navigateSpy).not.toHaveBeenCalled();
  });

  it('enviar() llama a submitAnswer y, al terminar, vuelve a pedir el detalle', async () => {
    const detailDespuesDeResponder: AssignmentDetail = {
      ...BASE_DETAIL,
      exercises: [
        BASE_DETAIL.exercises[0],
        { ...BASE_DETAIL.exercises[1], answered: true, answer_text: 'mi respuesta 2', verdict: 'incomplete', justification: 'Casi' },
      ],
    };

    let detailCalls = 0;
    const submitAnswer = vi.fn().mockReturnValue(
      of({ exercise_id: 'e2', verdict: 'incomplete', justification: 'Casi', answered_at: '2026-01-02' }),
    );

    TestBed.configureTestingModule({
      imports: [EjercicioComponent],
      providers: [
        provideRouter([]),
        {
          provide: AssignmentsApiService,
          useValue: {
            getDetail: () => {
              detailCalls += 1;
              return of(detailCalls === 1 ? BASE_DETAIL : detailDespuesDeResponder);
            },
            submitAnswer,
          },
        },
      ],
    });

    const fixture = TestBed.createComponent(EjercicioComponent);
    fixture.componentRef.setInput('assignmentId', 'a1');
    fixture.componentRef.setInput('position', '2');
    fixture.detectChanges();

    const component = fixture.componentInstance;
    component.answerText.set('mi respuesta 2');
    component.enviar();

    expect(submitAnswer).toHaveBeenCalledWith('a1', 'e2', 'mi respuesta 2');
    expect(detailCalls).toBe(2);
    expect(component.exercise()?.answered).toBe(true);
    expect(component.exercise()?.verdict).toBe('incomplete');
  });

  it('un 409 al enviar no rompe el componente: resincroniza en vez de mostrar un error sin manejar', () => {
    let detailCalls = 0;
    const submitAnswer = vi.fn().mockReturnValue(throwError(() => ({ status: 409 })));

    TestBed.configureTestingModule({
      imports: [EjercicioComponent],
      providers: [
        provideRouter([]),
        {
          provide: AssignmentsApiService,
          useValue: {
            getDetail: () => {
              detailCalls += 1;
              return of(BASE_DETAIL);
            },
            submitAnswer,
          },
        },
      ],
    });

    const fixture = TestBed.createComponent(EjercicioComponent);
    fixture.componentRef.setInput('assignmentId', 'a1');
    fixture.componentRef.setInput('position', '2');
    fixture.detectChanges();

    const component = fixture.componentInstance;
    component.answerText.set('respuesta tardia');
    component.enviar();

    expect(detailCalls).toBe(2); // carga inicial + resincronizacion tras el 409
    expect(component.submitError()).toBeNull();
  });
});

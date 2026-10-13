import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { ExerciseProgress } from '../../core/blocks-api.model';
import { StudentBlockAssignment, StudentSummary } from '../../core/users-api.model';
import { UsersApiService } from '../../core/users-api.service';
import { SupabaseService } from '../../core/supabase.service';
import { AlumnoDetalleComponent } from './alumno-detalle';

const ANA: StudentSummary = { id: 's1', name: 'Ana García', email: 'ana@empresa.com' };

function ejercicio(overrides: Partial<ExerciseProgress>): ExerciseProgress {
  return {
    exercise_id: 'e1',
    position: 1,
    name: 'nombre del ejercicio',
    type: 'knowledge',
    statement: 'enunciado',
    answered: false,
    verdict: null,
    answer_text: null,
    justification: null,
    ...overrides,
  };
}

const SIN_EMPEZAR: StudentBlockAssignment = {
  assignment_id: 'a1',
  block_id: 'b1',
  block_name: 'Conceptos de Angular',
  exercises: [ejercicio({ exercise_id: 'e1', position: 1 }), ejercicio({ exercise_id: 'e2', position: 2 })],
};

const EN_CURSO: StudentBlockAssignment = {
  assignment_id: 'a2',
  block_id: 'b2',
  block_name: 'Fundamentos de pokemon-open-spec',
  exercises: [
    ejercicio({
      exercise_id: 'e1',
      position: 1,
      name: 'Señales computadas',
      type: 'knowledge',
      statement: '¿Qué hace computed()?',
      answered: true,
      verdict: 'correct',
      answer_text: 'computed crea una señal derivada.',
      justification: 'Explica bien que es derivada.',
    }),
    ejercicio({
      exercise_id: 'e2',
      position: 2,
      name: 'Pokémon inexistente devuelve 500',
      type: 'debug',
      statement: 'Un pokémon que no existe devuelve 500.',
      answered: true,
      verdict: 'incorrect',
      answer_text: 'El problema está en la API.',
      justification: 'No identifica la causa.',
    }),
    ejercicio({ exercise_id: 'e3', position: 3 }),
  ],
};

const COMPLETADO: StudentBlockAssignment = {
  assignment_id: 'a3',
  block_id: 'b3',
  block_name: 'Introducción a FastAPI',
  exercises: [
    ejercicio({ exercise_id: 'e1', position: 1, answered: true, verdict: 'correct', answer_text: 'ok' }),
    ejercicio({ exercise_id: 'e2', position: 2, answered: true, verdict: 'incomplete', answer_text: 'ok' }),
  ],
};

describe('AlumnoDetalleComponent', () => {
  function createComponent(assignments: StudentBlockAssignment[]) {
    TestBed.configureTestingModule({
      imports: [AlumnoDetalleComponent],
      providers: [
        provideRouter([]),
        { provide: SupabaseService, useValue: { signOut: async () => undefined } },
        {
          provide: UsersApiService,
          useValue: {
            listStudents: vi.fn().mockReturnValue(of([ANA])),
            getBlocks: vi.fn().mockReturnValue(of(assignments)),
          },
        },
      ],
    });
    const fixture = TestBed.createComponent(AlumnoDetalleComponent);
    fixture.componentRef.setInput('studentId', 's1');
    fixture.detectChanges();
    return fixture;
  }

  it('cabecera: muestra nombre, email y el numero de bloques asignados', () => {
    const fixture = createComponent([SIN_EMPEZAR, EN_CURSO, COMPLETADO]);
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Ana García');
    expect(text).toContain('ana@empresa.com');
    expect(text).toContain('3 bloques de ejercicios asignados');
  });

  it('bloque sin empezar: estado "Sin empezar · 0 de 2" y "Sin respuestas"', () => {
    const fixture = createComponent([SIN_EMPEZAR]);
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Sin empezar · 0 de 2');
    expect(text).toContain('Sin respuestas');
  });

  it('bloque en curso: estado "En curso · 2 de 3" y contadores de veredictos', () => {
    const fixture = createComponent([EN_CURSO]);
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('En curso · 2 de 3');
    expect(text).toContain('1 correcta · 0 incompletas · 1 incorrecta');
  });

  it('bloque completado: estado "Completado · 2 de 2" y contadores de veredictos', () => {
    const fixture = createComponent([COMPLETADO]);
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Completado · 2 de 2');
    expect(text).toContain('1 correcta · 1 incompleta · 0 incorrectas');
  });

  it('al expandir un bloque, muestra el detalle de cada ejercicio (tipo, enunciado, respuesta, veredicto, justificacion o "Sin responder")', () => {
    const fixture = createComponent([EN_CURSO]);
    const el = fixture.nativeElement as HTMLElement;

    const toggle = Array.from(el.querySelectorAll('button')).find((b) =>
      b.textContent?.includes('Fundamentos de pokemon-open-spec'),
    );
    toggle!.click();
    fixture.detectChanges();

    const text = el.textContent ?? '';
    expect(text).toContain('Señales computadas');
    expect(text).toContain('computed crea una señal derivada.');
    expect(text).toContain('Correcta');
    expect(text).toContain('Explica bien que es derivada.');
    expect(text).toContain('Pokémon inexistente devuelve 500');
    expect(text).toContain('Incorrecta');
    expect(text).toContain('Sin responder');
    expect(text).toContain('Ver detalle del bloque');
  });
});

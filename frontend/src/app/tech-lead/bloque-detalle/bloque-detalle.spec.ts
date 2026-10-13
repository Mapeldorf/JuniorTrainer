import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { BlocksApiService } from '../../core/blocks-api.service';
import { BlockDetail, StudentProgress } from '../../core/blocks-api.model';
import { UsersApiService } from '../../core/users-api.service';
import { StudentSummary } from '../../core/users-api.model';
import { SupabaseService } from '../../core/supabase.service';
import { BloqueDetalleComponent } from './bloque-detalle';

const BLOCK: BlockDetail = {
  id: 'b1',
  name: 'Bloque 1',
  created_at: '2026-01-01',
  updated_at: '2026-01-01',
  deleted_at: null,
  resolved: false,
  exercises: [
    {
      position: 1,
      exercise: { id: 'e1', type: 'knowledge', name: 'Rebase en Git', statement: 'Explica git rebase', code: [], expected_answer: null },
      exercise_deleted: false,
    },
  ],
};

const PROGRESS: StudentProgress[] = [
  {
    student_id: 's1',
    student_name: 'Ana',
    assignment_id: 'a1',
    exercises: [
      {
        exercise_id: 'e1',
        position: 1,
        name: 'Rebase en Git',
        type: 'knowledge',
        statement: 'Explica git rebase',
        answered: true,
        verdict: 'correct',
        answer_text: 'mi respuesta',
        justification: 'bien explicado',
      },
    ],
  },
];

const STUDENTS: StudentSummary[] = [
  { id: 's1', name: 'Ana', email: 'ana@example.com' },
  { id: 's2', name: 'Bea', email: 'bea@example.com' },
];

describe('BloqueDetalleComponent', () => {
  function createComponent(opts: {
    block?: BlockDetail;
    progress?: StudentProgress[];
    students?: StudentSummary[];
    assign?: ReturnType<typeof vi.fn>;
    deleteFn?: ReturnType<typeof vi.fn>;
  }) {
    TestBed.configureTestingModule({
      imports: [BloqueDetalleComponent],
      providers: [
        provideRouter([]),
        { provide: SupabaseService, useValue: { signOut: async () => undefined } },
        {
          provide: BlocksApiService,
          useValue: {
            getDetail: vi.fn().mockReturnValue(of(opts.block ?? BLOCK)),
            getProgress: vi.fn().mockReturnValue(of(opts.progress ?? PROGRESS)),
            assign: opts.assign ?? vi.fn().mockReturnValue(of({ results: [] })),
            delete: opts.deleteFn ?? vi.fn().mockReturnValue(of({ ...BLOCK, deleted_at: '2026-03-01' })),
          },
        },
        { provide: UsersApiService, useValue: { listStudents: vi.fn().mockReturnValue(of(opts.students ?? STUDENTS)) } },
      ],
    });
    const fixture = TestBed.createComponent(BloqueDetalleComponent);
    fixture.componentRef.setInput('blockId', 'b1');
    fixture.detectChanges();
    return fixture;
  }

  it('muestra la cabecera y "Editar bloque"/"Eliminar bloque" cuando el bloque no esta resuelto ni eliminado', () => {
    const fixture = createComponent({});
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Bloque 1');
    expect(text).toContain('Editar bloque');
    expect(text).toContain('Eliminar bloque');

    const buttons = Array.from(
      fixture.nativeElement.querySelectorAll('button'),
    ) as HTMLButtonElement[];
    const editBtn = buttons.find((b) => b.textContent?.includes('Editar bloque'));
    expect(editBtn?.disabled).toBe(false);
  });

  it('deshabilita "Editar bloque" cuando el bloque esta resuelto', () => {
    const fixture = createComponent({ block: { ...BLOCK, resolved: true } });
    const buttons = Array.from(
      fixture.nativeElement.querySelectorAll('button'),
    ) as HTMLButtonElement[];
    const editBtn = buttons.find((b) => b.textContent?.includes('Editar bloque'));
    expect(editBtn?.disabled).toBe(true);
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Resuelto · no editable');
  });

  it('un bloque eliminado no muestra "Editar bloque", "Eliminar bloque" ni "Asignar a más alumnos"', () => {
    const fixture = createComponent({ block: { ...BLOCK, deleted_at: '2026-02-01' } });
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).not.toContain('Editar bloque');
    expect(text).not.toContain('Eliminar bloque');
    expect(text).not.toContain('Asignar a más alumnos');
  });

  it('eliminar() pide confirmacion: si se confirma, llama a delete', async () => {
    const deleteFn = vi.fn().mockReturnValue(of({ ...BLOCK, deleted_at: '2026-03-01' }));
    const fixture = createComponent({ deleteFn });
    const component = fixture.componentInstance;
    vi.spyOn(component, 'confirmarEliminar').mockResolvedValue(true);

    await component.eliminar();

    expect(deleteFn).toHaveBeenCalledWith('b1');
  });

  it('eliminar() no llama a delete si no se confirma', async () => {
    const deleteFn = vi.fn().mockReturnValue(of({ ...BLOCK, deleted_at: '2026-03-01' }));
    const fixture = createComponent({ deleteFn });
    const component = fixture.componentInstance;
    vi.spyOn(component, 'confirmarEliminar').mockResolvedValue(false);

    await component.eliminar();

    expect(deleteFn).not.toHaveBeenCalled();
  });

  it('al desplegar un alumno, muestra el detalle de su ejercicio (respuesta, veredicto, justificacion)', () => {
    const fixture = createComponent({});
    const el = fixture.nativeElement as HTMLElement;
    const toggle = Array.from(el.querySelectorAll('button')).find((b) => b.textContent?.includes('Ana'));
    toggle!.dispatchEvent(new Event('click'));
    fixture.detectChanges();

    const text = el.textContent ?? '';
    expect(text).toContain('mi respuesta');
    expect(text).toContain('bien explicado');
  });

  it('la seccion "Asignar a mas alumnos" excluye a los ya asignados', () => {
    const fixture = createComponent({});
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Bea');
    // Ana ya esta asignada: no debe aparecer en la checklist de "Asignar a mas alumnos"
    // (solo en la seccion de alumnos asignados, que ya se comprobo arriba).
    const checkboxes = fixture.nativeElement.querySelectorAll(
      'input[type="checkbox"]',
    ) as NodeListOf<HTMLInputElement>;
    expect(checkboxes.length).toBe(1);
  });
});

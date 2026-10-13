import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { BlocksApiService } from '../../core/blocks-api.service';
import { BlockDetail } from '../../core/blocks-api.model';
import { GenerationsApiService } from '../../core/generations-api.service';
import { SavedExerciseListItem } from '../../core/generations-api.model';
import { SupabaseService } from '../../core/supabase.service';
import { BloqueEditarComponent } from './bloque-editar';

const CATALOG_ITEM: SavedExerciseListItem = {
  id: 'e1',
  type: 'knowledge',
  name: 'Rebase en Git',
  statement: 'Explica que hace git rebase',
  code: [],
  expected_answer: 'respuesta',
  technologies: ['Git'],
  repo_path: null,
  block_usage_count: 0,
};

const BLOCK_DETAIL: BlockDetail = {
  id: 'b1',
  name: 'Bloque 1',
  created_at: '2026-01-01',
  updated_at: '2026-01-01',
  deleted_at: null,
  resolved: false,
  exercises: [
    {
      position: 1,
      exercise: { id: 'e1', type: 'knowledge', name: 'Rebase en Git', statement: 'Explica que hace git rebase', code: [], expected_answer: 'respuesta' },
      exercise_deleted: false,
    },
  ],
};

describe('BloqueEditarComponent', () => {
  function createComponent(opts: {
    blockId?: string;
    listSaved?: ReturnType<typeof vi.fn>;
    getDetail?: ReturnType<typeof vi.fn>;
    create?: ReturnType<typeof vi.fn>;
    update?: ReturnType<typeof vi.fn>;
  }) {
    TestBed.configureTestingModule({
      imports: [BloqueEditarComponent],
      providers: [
        provideRouter([]),
        { provide: SupabaseService, useValue: { signOut: async () => undefined } },
        {
          provide: GenerationsApiService,
          useValue: { listSaved: opts.listSaved ?? vi.fn().mockReturnValue(of([CATALOG_ITEM])) },
        },
        {
          provide: BlocksApiService,
          useValue: {
            getDetail: opts.getDetail ?? vi.fn().mockReturnValue(of(BLOCK_DETAIL)),
            create: opts.create ?? vi.fn().mockReturnValue(of(BLOCK_DETAIL)),
            update: opts.update ?? vi.fn().mockReturnValue(of(BLOCK_DETAIL)),
          },
        },
      ],
    });
    const fixture = TestBed.createComponent(BloqueEditarComponent);
    if (opts.blockId) {
      fixture.componentRef.setInput('blockId', opts.blockId);
    }
    fixture.detectChanges();
    return fixture;
  }

  it('modo creacion: formulario vacio, boton "Crear bloque" deshabilitado con 0 ejercicios marcados', () => {
    const fixture = createComponent({});
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Crear bloque');
    const buttons = Array.from(
      fixture.nativeElement.querySelectorAll('button'),
    ) as HTMLButtonElement[];
    const button = buttons.find((b) => b.textContent?.includes('Crear bloque'));
    expect(button?.disabled).toBe(true);
  });

  it('modo edicion: precarga nombre y ejercicios marcados, boton "Guardar cambios"', () => {
    const fixture = createComponent({ blockId: 'b1' });
    const component = fixture.componentInstance;
    expect(component.name()).toBe('Bloque 1');
    expect(component.selectedIds()).toEqual(['e1']);
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Guardar cambios');
  });

  it('un ejercicio marcado habilita el boton (sin ejercicios eliminados)', () => {
    const fixture = createComponent({ blockId: 'b1' });
    fixture.detectChanges();
    expect(fixture.componentInstance.canSave).toBe(true);
  });

  it('un ejercicio eliminado en la composicion deshabilita el boton hasta desmarcarlo', () => {
    const detailWithDeleted: BlockDetail = {
      ...BLOCK_DETAIL,
      exercises: [
        ...BLOCK_DETAIL.exercises,
        {
          position: 2,
          exercise: { id: 'e2', type: 'debug', name: 'Ejercicio eliminado', statement: 'Ejercicio eliminado', code: [], expected_answer: null },
          exercise_deleted: true,
        },
      ],
    };
    const fixture = createComponent({
      blockId: 'b1',
      getDetail: vi.fn().mockReturnValue(of(detailWithDeleted)),
    });
    const component = fixture.componentInstance;
    expect(component.hasDeletedSelected).toBe(true);
    expect(component.canSave).toBe(false);

    component.toggle('e2');
    fixture.detectChanges();
    expect(component.hasDeletedSelected).toBe(false);
    expect(component.canSave).toBe(true);
  });
});

import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { BlocksApiService } from '../../core/blocks-api.service';
import { BlockSummary } from '../../core/blocks-api.model';
import { SupabaseService } from '../../core/supabase.service';
import { BloquesComponent } from './bloques';

const ACTIVO: BlockSummary = {
  id: 'b1',
  name: 'Bloque 1',
  created_at: '2026-01-01',
  updated_at: '2026-01-01',
  deleted_at: null,
  exercise_count: 3,
  assigned_students: [{ id: 's1', name: 'Ana' }],
  resolved: false,
};

const ELIMINADO: BlockSummary = {
  ...ACTIVO,
  id: 'b2',
  name: 'Bloque 2',
  deleted_at: '2026-02-01',
  assigned_students: [],
};

describe('BloquesComponent', () => {
  function createComponent(opts: { list?: ReturnType<typeof vi.fn> }) {
    const listFn =
      opts.list ??
      vi.fn((deleted: boolean) => of(deleted ? [ELIMINADO] : [ACTIVO]));
    TestBed.configureTestingModule({
      imports: [BloquesComponent],
      providers: [
        provideRouter([]),
        { provide: SupabaseService, useValue: { signOut: async () => undefined } },
        { provide: BlocksApiService, useValue: { list: listFn } },
      ],
    });
    const fixture = TestBed.createComponent(BloquesComponent);
    fixture.detectChanges();
    return fixture;
  }

  it('muestra los bloques activos con su numero de ejercicios y alumnos asignados', () => {
    const fixture = createComponent({});
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Bloque 1');
    expect(text).toContain('Ana');
  });

  it('marca "Resuelto · no editable" cuando el bloque esta resuelto', () => {
    const resolved: BlockSummary = { ...ACTIVO, resolved: true };
    const fixture = createComponent({ list: vi.fn(() => of([resolved])) });
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Resuelto · no editable');
  });

  it('muestra el estado vacio cuando no hay bloques activos', () => {
    const fixture = createComponent({ list: vi.fn(() => of([])) });
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('No hay ningún bloque todavía');
  });

  it('la seccion de bloques eliminados aparece colapsada y muestra el conteo', () => {
    const fixture = createComponent({});
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Bloques de ejercicios eliminados (1)');
    expect(text).not.toContain('Bloque 2');
  });

  it('al desplegar, la seccion de eliminados muestra el bloque de solo lectura con "Ver resultados"', () => {
    const fixture = createComponent({});
    const el = fixture.nativeElement as HTMLElement;
    const toggle = Array.from(el.querySelectorAll('button')).find((b) =>
      b.textContent?.includes('Bloques de ejercicios eliminados'),
    );
    toggle!.click();
    fixture.detectChanges();

    const text = el.textContent ?? '';
    expect(text).toContain('Bloque 2');
    expect(text).toContain('Ver resultados');
  });
});

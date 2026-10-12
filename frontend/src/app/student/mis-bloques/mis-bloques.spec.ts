import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { AssignmentsApiService } from '../../core/assignments-api.service';
import { AssignmentSummary } from '../../core/assignments-api.model';
import { SupabaseService } from '../../core/supabase.service';
import { MisBloquesComponent } from './mis-bloques';

describe('MisBloquesComponent', () => {
  const assignments: AssignmentSummary[] = [
    { id: 'a1', block_name: 'Bloque sin empezar', assigned_at: '2026-01-01', answered_count: 0, total_count: 3 },
    { id: 'a2', block_name: 'Bloque a medias', assigned_at: '2026-01-02', answered_count: 1, total_count: 3 },
    { id: 'a3', block_name: 'Bloque terminado', assigned_at: '2026-01-03', answered_count: 2, total_count: 2 },
  ];

  function createComponent(summaries: AssignmentSummary[]) {
    TestBed.configureTestingModule({
      imports: [MisBloquesComponent],
      providers: [
        provideRouter([]),
        { provide: AssignmentsApiService, useValue: { listMine: () => of(summaries) } },
        { provide: SupabaseService, useValue: { signOut: async () => undefined } },
      ],
    });
    const fixture = TestBed.createComponent(MisBloquesComponent);
    fixture.detectChanges();
    return fixture;
  }

  it('separa pendientes y hechos, y distingue Empezar de Continuar', () => {
    const fixture = createComponent(assignments);
    const component = fixture.componentInstance;

    expect(component.pendientes().map((a) => a.id)).toEqual(['a1', 'a2']);
    expect(component.hechos().map((a) => a.id)).toEqual(['a3']);
    expect(component.pendienteLabel(assignments[0])).toBe('Empezar');
    expect(component.pendienteLabel(assignments[1])).toBe('Continuar');
  });

  it('renderiza el nombre de cada bloque en la vista', () => {
    const fixture = createComponent(assignments);
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Bloque sin empezar');
    expect(text).toContain('Bloque a medias');
    expect(text).toContain('Bloque terminado');
    expect(text).toContain('Empezar');
    expect(text).toContain('Continuar');
    expect(text).toContain('Consultar');
  });

  it('sin asignaciones, ambas listas estan vacias', () => {
    const fixture = createComponent([]);
    const component = fixture.componentInstance;
    expect(component.pendientes()).toEqual([]);
    expect(component.hechos()).toEqual([]);
  });
});

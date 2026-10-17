import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ExerciseDetailComponent } from './exercise-detail';
import { SavedExerciseListItem } from './generations-api.model';

const EXERCISE: SavedExerciseListItem = {
  id: 'e1',
  type: 'debug',
  name: 'Rebase en Git',
  statement: 'Explica que hace git rebase',
  code: [{ file: 'main.py', code: 'print("hola")' }],
  expected_answer: 'respuesta esperada',
  technologies: ['Git', 'Python'],
  repo: 'org/repo',
  block_usage_count: 2,
};

describe('ExerciseDetailComponent', () => {
  function createComponent(exercise: SavedExerciseListItem | null): ComponentFixture<ExerciseDetailComponent> {
    TestBed.configureTestingModule({ imports: [ExerciseDetailComponent] });
    const fixture = TestBed.createComponent(ExerciseDetailComponent);
    fixture.componentRef.setInput('exercise', exercise);
    fixture.detectChanges();
    return fixture;
  }

  it('no renderiza nada sin ejercicio seleccionado', () => {
    const fixture = createComponent(null);
    const el = fixture.nativeElement as HTMLElement;
    expect(el.querySelector('[role="dialog"]')).toBeNull();
  });

  it('muestra todos los campos del ejercicio', () => {
    const fixture = createComponent(EXERCISE);
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';

    expect(text).toContain(EXERCISE.name);
    expect(text).toContain('Depuración');
    expect(text).toContain('Git, Python');
    expect(text).toContain(EXERCISE.repo!);
    expect(text).toContain(EXERCISE.statement);
    expect(text).toContain('print("hola")');
    expect(text).toContain(EXERCISE.expected_answer!);
  });

  it('indica la ausencia de respuesta esperada', () => {
    const fixture = createComponent({ ...EXERCISE, expected_answer: null });
    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Sin respuesta esperada.');
  });

  it('al abrirse, el foco inicial recae en el boton de cierre', () => {
    const fixture = createComponent(EXERCISE);
    const el = fixture.nativeElement as HTMLElement;
    const closeButton = Array.from(el.querySelectorAll('button')).find((b) =>
      b.textContent?.includes('Cerrar'),
    );
    expect(document.activeElement).toBe(closeButton);
  });

  it('pulsar Cerrar emite el cierre', () => {
    const fixture = createComponent(EXERCISE);
    let closed = 0;
    fixture.componentInstance.closed.subscribe(() => (closed += 1));

    const el = fixture.nativeElement as HTMLElement;
    const closeButton = Array.from(el.querySelectorAll('button')).find((b) =>
      b.textContent?.includes('Cerrar'),
    );
    closeButton!.click();

    expect(closed).toBe(1);
  });

  it('Escape sobre el panel emite el cierre', () => {
    const fixture = createComponent(EXERCISE);
    let closed = 0;
    fixture.componentInstance.closed.subscribe(() => (closed += 1));

    const el = fixture.nativeElement as HTMLElement;
    const dialog = el.querySelector('[role="dialog"]') as HTMLElement;
    dialog.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));

    expect(closed).toBe(1);
  });

  it('clic en el fondo emite el cierre', () => {
    const fixture = createComponent(EXERCISE);
    let closed = 0;
    fixture.componentInstance.closed.subscribe(() => (closed += 1));

    const el = fixture.nativeElement as HTMLElement;
    const dialog = el.querySelector('[role="dialog"]') as HTMLElement;
    dialog.click();

    expect(closed).toBe(1);
  });

  it('clic dentro de la tarjeta no emite el cierre', () => {
    const fixture = createComponent(EXERCISE);
    let closed = 0;
    fixture.componentInstance.closed.subscribe(() => (closed += 1));

    const el = fixture.nativeElement as HTMLElement;
    const card = el.querySelector('[role="dialog"] > div') as HTMLElement;
    card.click();

    expect(closed).toBe(0);
  });
});
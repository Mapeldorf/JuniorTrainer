import { ComponentFixture, TestBed } from '@angular/core/testing';
import { PaginationComponent } from './pagination';

describe('PaginationComponent', () => {
  function createComponent(page: number, totalPages: number): ComponentFixture<PaginationComponent> {
    TestBed.configureTestingModule({ imports: [PaginationComponent] });
    const fixture = TestBed.createComponent(PaginationComponent);
    fixture.componentRef.setInput('page', page);
    fixture.componentRef.setInput('totalPages', totalPages);
    fixture.detectChanges();
    return fixture;
  }

  function buttonByLabel(fixture: ComponentFixture<PaginationComponent>, label: string) {
    return (fixture.nativeElement as HTMLElement).querySelector<HTMLButtonElement>(
      `[aria-label="${label}"]`,
    );
  }

  it('no renderiza nada cuando hay una sola pagina', () => {
    const fixture = createComponent(1, 1);
    expect((fixture.nativeElement as HTMLElement).querySelector('nav')).toBeNull();
  });

  it('renderiza un numero por pagina y marca la actual', () => {
    const fixture = createComponent(2, 3);
    const el = fixture.nativeElement as HTMLElement;
    const numbers = Array.from(el.querySelectorAll('button')).map((b) => b.textContent?.trim());
    expect(numbers).toEqual(expect.arrayContaining(['1', '2', '3']));
    const current = el.querySelector('[aria-current="page"]');
    expect(current?.textContent?.trim()).toBe('2');
  });

  it('en la primera pagina deshabilita Anterior', () => {
    const fixture = createComponent(1, 3);
    expect(buttonByLabel(fixture, 'Página anterior')?.disabled).toBe(true);
    expect(buttonByLabel(fixture, 'Página siguiente')?.disabled).toBe(false);
  });

  it('en la ultima pagina deshabilita Siguiente', () => {
    const fixture = createComponent(3, 3);
    expect(buttonByLabel(fixture, 'Página siguiente')?.disabled).toBe(true);
    expect(buttonByLabel(fixture, 'Página anterior')?.disabled).toBe(false);
  });

  it('pulsar un numero emite pageChange con esa pagina', () => {
    const fixture = createComponent(1, 3);
    const emitted: number[] = [];
    fixture.componentInstance.pageChange.subscribe((p) => emitted.push(p));

    buttonByLabel(fixture, 'Página 3')!.click();

    expect(emitted).toEqual([3]);
  });

  it('pulsar Siguiente emite la pagina siguiente', () => {
    const fixture = createComponent(2, 3);
    const emitted: number[] = [];
    fixture.componentInstance.pageChange.subscribe((p) => emitted.push(p));

    buttonByLabel(fixture, 'Página siguiente')!.click();

    expect(emitted).toEqual([3]);
  });

  it('pulsar Anterior emite la pagina anterior', () => {
    const fixture = createComponent(2, 3);
    const emitted: number[] = [];
    fixture.componentInstance.pageChange.subscribe((p) => emitted.push(p));

    buttonByLabel(fixture, 'Página anterior')!.click();

    expect(emitted).toEqual([1]);
  });

  it('los numeros y los extremos respetan el lenguaje visual del tema', () => {
    const fixture = createComponent(2, 3);
    const el = fixture.nativeElement as HTMLElement;

    const inactiveNumber = buttonByLabel(fixture, 'Página 3')!;
    expect(inactiveNumber.className).toContain('focus-ring');
    expect(inactiveNumber.className).toContain('text-content');

    const current = el.querySelector('[aria-current="page"]') as HTMLButtonElement;
    expect(current.className).toContain('bg-primary');

    const prev = buttonByLabel(fixture, 'Página anterior')!;
    expect(prev.className).toContain('btn-secondary');
  });
});
import { TestBed } from '@angular/core/testing';
import { Technology } from '../generations-api.model';
import { TechnologyMultiselectComponent } from './technology-multiselect';

const CATALOG: Technology[] = [
  { id: '1', name: 'Angular' },
  { id: '2', name: 'RxJS' },
  { id: '3', name: 'NgRx' },
];

describe('TechnologyMultiselectComponent', () => {
  function create() {
    const fixture = TestBed.createComponent(TechnologyMultiselectComponent);
    fixture.componentRef.setInput('technologies', CATALOG);
    fixture.detectChanges();
    return fixture;
  }

  function combo(fixture: ReturnType<typeof create>): HTMLElement {
    return fixture.nativeElement.querySelector('[role="combobox"]') as HTMLElement;
  }

  it('muestra el placeholder cuando no hay ninguna tecnologia seleccionada', () => {
    const fixture = create();
    expect(combo(fixture).textContent).toContain('Selecciona tecnologías');
  });

  it('al seleccionar una opcion actualiza el modelo y muestra un chip', () => {
    const fixture = create();
    combo(fixture).click();
    fixture.detectChanges();

    const options = fixture.nativeElement.querySelectorAll('[role="option"]');
    (options[0] as HTMLElement).click();
    fixture.detectChanges();

    expect(fixture.componentInstance.selected()).toEqual(['Angular']);
    expect(combo(fixture).textContent).toContain('Angular');
  });

  it('permite seleccionar varias tecnologias a la vez', () => {
    const fixture = create();
    combo(fixture).click();
    fixture.detectChanges();

    const options = fixture.nativeElement.querySelectorAll('[role="option"]');
    (options[0] as HTMLElement).click();
    fixture.detectChanges();
    (options[1] as HTMLElement).click();
    fixture.detectChanges();

    expect(fixture.componentInstance.selected()).toEqual(['Angular', 'RxJS']);
  });

  it('al volver a pulsar una opcion seleccionada la deselecciona', () => {
    const fixture = create();
    combo(fixture).click();
    fixture.detectChanges();

    const option = fixture.nativeElement.querySelector('[role="option"]') as HTMLElement;
    option.click();
    fixture.detectChanges();
    option.click();
    fixture.detectChanges();

    expect(fixture.componentInstance.selected()).toEqual([]);
  });

  it('el boton del chip quita la tecnologia seleccionada', () => {
    const fixture = create();
    fixture.componentInstance.selected.set(['RxJS']);
    fixture.detectChanges();

    const removeButton = fixture.nativeElement.querySelector(
      'button[aria-label="Quitar RxJS"]',
    ) as HTMLButtonElement;
    removeButton.click();
    fixture.detectChanges();

    expect(fixture.componentInstance.selected()).toEqual([]);
  });

  it('el buscador filtra las opciones del catalogo', () => {
    const fixture = create();
    combo(fixture).click();
    fixture.detectChanges();

    const search = fixture.nativeElement.querySelector('input[type="search"]') as HTMLInputElement;
    search.value = 'ang';
    search.dispatchEvent(new Event('input'));
    fixture.detectChanges();

    const options = fixture.nativeElement.querySelectorAll('[role="option"]');
    expect(options.length).toBe(1);
    expect((options[0] as HTMLElement).textContent).toContain('Angular');
  });

  it('con el teclado, ArrowDown y Enter seleccionan la opcion activa', () => {
    const fixture = create();
    combo(fixture).click();
    fixture.detectChanges();

    combo(fixture).dispatchEvent(new KeyboardEvent('keydown', { key: 'ArrowDown', bubbles: true }));
    combo(fixture).dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
    fixture.detectChanges();

    expect(fixture.componentInstance.selected()).toEqual(['Angular']);
  });

  it('Escape cierra el panel', () => {
    const fixture = create();
    combo(fixture).click();
    fixture.detectChanges();
    expect(fixture.componentInstance.open()).toBe(true);

    combo(fixture).dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    fixture.detectChanges();

    expect(fixture.componentInstance.open()).toBe(false);
  });

  it('muestra el estado vacio cuando el catalogo no tiene coincidencias', () => {
    const fixture = create();
    combo(fixture).click();
    fixture.detectChanges();

    const search = fixture.nativeElement.querySelector('input[type="search"]') as HTMLInputElement;
    search.value = 'zzz';
    search.dispatchEvent(new Event('input'));
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('Sin resultados');
  });

  it('muestra el estado de carga', () => {
    const fixture = TestBed.createComponent(TechnologyMultiselectComponent);
    fixture.componentRef.setInput('technologies', CATALOG);
    fixture.componentRef.setInput('loading', true);
    fixture.detectChanges();

    combo(fixture).click();
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('Cargando');
  });

  it('muestra el estado de error', () => {
    const fixture = TestBed.createComponent(TechnologyMultiselectComponent);
    fixture.componentRef.setInput('technologies', []);
    fixture.componentRef.setInput('error', true);
    fixture.detectChanges();

    combo(fixture).click();
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('No se ha podido cargar el catálogo');
  });
});
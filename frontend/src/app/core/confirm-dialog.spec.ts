import { TestBed } from '@angular/core/testing';
import { ConfirmDialogComponent } from './confirm-dialog';
import { ConfirmDialogService } from './confirm-dialog.service';

const OPTIONS = {
  title: 'Eliminar bloque',
  message: '¿Eliminar el bloque "Angular basico"?',
  confirmLabel: 'Eliminar',
  cancelLabel: 'Cancelar',
  destructive: true,
};

describe('ConfirmDialogComponent', () => {
  function createComponent() {
    TestBed.configureTestingModule({ imports: [ConfirmDialogComponent] });
    const fixture = TestBed.createComponent(ConfirmDialogComponent);
    fixture.detectChanges();
    const service = TestBed.inject(ConfirmDialogService);
    return { fixture, service };
  }

  it('no renderiza nada sin peticion activa', () => {
    const { fixture } = createComponent();
    const el = fixture.nativeElement as HTMLElement;
    expect(el.querySelector('[role="alertdialog"]')).toBeNull();
  });

  it('con una peticion activa, renderiza el titulo, el mensaje y los textos de los botones', () => {
    const { fixture, service } = createComponent();
    service.confirm(OPTIONS);
    fixture.detectChanges();

    const el = fixture.nativeElement as HTMLElement;
    expect(el.querySelector('h2')?.textContent).toContain(OPTIONS.title);
    expect(el.querySelector('p')?.textContent).toContain(OPTIONS.message);
    const buttons = Array.from(el.querySelectorAll('button'));
    expect(buttons.some((b) => b.textContent?.includes(OPTIONS.cancelLabel))).toBe(true);
    expect(buttons.some((b) => b.textContent?.includes(OPTIONS.confirmLabel))).toBe(true);
  });

  it('pulsar confirmar resuelve la peticion como true', async () => {
    const { fixture, service } = createComponent();
    const promise = service.confirm(OPTIONS);
    fixture.detectChanges();

    const el = fixture.nativeElement as HTMLElement;
    const confirmButton = Array.from(el.querySelectorAll('button')).find((b) =>
      b.textContent?.includes(OPTIONS.confirmLabel),
    );
    confirmButton!.click();

    expect(await promise).toBe(true);
  });

  it('pulsar cancelar resuelve la peticion como false', async () => {
    const { fixture, service } = createComponent();
    const promise = service.confirm(OPTIONS);
    fixture.detectChanges();

    const el = fixture.nativeElement as HTMLElement;
    const cancelButton = Array.from(el.querySelectorAll('button')).find((b) =>
      b.textContent?.includes(OPTIONS.cancelLabel),
    );
    cancelButton!.click();

    expect(await promise).toBe(false);
  });

  it('al abrirse, el foco inicial recae en el boton de cancelar', () => {
    const { fixture, service } = createComponent();
    service.confirm(OPTIONS);
    fixture.detectChanges();

    const el = fixture.nativeElement as HTMLElement;
    const cancelButton = Array.from(el.querySelectorAll('button')).find((b) =>
      b.textContent?.includes(OPTIONS.cancelLabel),
    );
    expect(document.activeElement).toBe(cancelButton);
  });

  it('Escape sobre el dialogo resuelve como cancelado', async () => {
    const { fixture, service } = createComponent();
    const promise = service.confirm(OPTIONS);
    fixture.detectChanges();

    const el = fixture.nativeElement as HTMLElement;
    const dialog = el.querySelector('[role="alertdialog"]') as HTMLElement;
    dialog.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));

    expect(await promise).toBe(false);
  });
});

import { TestBed } from '@angular/core/testing';
import { ConfirmDialogService } from './confirm-dialog.service';

const OPTIONS = {
  title: 'Eliminar',
  message: '¿Seguro?',
  confirmLabel: 'Eliminar',
  cancelLabel: 'Cancelar',
};

describe('ConfirmDialogService', () => {
  function createService(): ConfirmDialogService {
    TestBed.configureTestingModule({});
    return TestBed.inject(ConfirmDialogService);
  }

  it('confirm() fija la peticion y resuelve true al llamar a resolveConfirm()', async () => {
    const service = createService();
    const promise = service.confirm(OPTIONS);

    expect(service.request()).toEqual(OPTIONS);

    service.resolveConfirm();

    expect(await promise).toBe(true);
    expect(service.request()).toBeNull();
  });

  it('confirm() resuelve false al llamar a resolveCancel()', async () => {
    const service = createService();
    const promise = service.confirm(OPTIONS);

    service.resolveCancel();

    expect(await promise).toBe(false);
    expect(service.request()).toBeNull();
  });

  it('una segunda llamada a confirm() con una peticion activa resuelve la primera como false', async () => {
    const service = createService();
    const first = service.confirm(OPTIONS);
    const second = service.confirm({ ...OPTIONS, title: 'Otra' });

    expect(await first).toBe(false);
    expect(service.request()).toEqual({ ...OPTIONS, title: 'Otra' });

    service.resolveConfirm();
    expect(await second).toBe(true);
  });
});

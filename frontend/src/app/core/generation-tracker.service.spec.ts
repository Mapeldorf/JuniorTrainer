import { GenerationTrackerService } from './generation-tracker.service';

describe('GenerationTrackerService', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    sessionStorage.clear();
  });

  it('add() y list() acumulan los ids sin duplicados', () => {
    const service = new GenerationTrackerService();

    service.add('g1');
    service.add('g2');
    service.add('g1');

    expect(service.list()).toEqual(['g1', 'g2']);
  });

  it('remove() quita solo el id indicado', () => {
    const service = new GenerationTrackerService();
    service.add('g1');
    service.add('g2');

    service.remove('g1');

    expect(service.list()).toEqual(['g2']);
  });

  it('persiste los ids en sessionStorage y los recupera en una instancia nueva', () => {
    const service = new GenerationTrackerService();
    service.add('g1');

    expect(JSON.parse(sessionStorage.getItem('pendingGenerationIds') ?? '[]')).toEqual(['g1']);

    const restored = new GenerationTrackerService();
    expect(restored.list()).toEqual(['g1']);
  });

  it('degrada a memoria sin lanzar cuando sessionStorage no esta disponible', () => {
    vi.stubGlobal('sessionStorage', undefined);
    const service = new GenerationTrackerService();

    expect(() => service.add('g1')).not.toThrow();
    expect(service.list()).toEqual(['g1']);
    expect(() => service.remove('g1')).not.toThrow();
    expect(service.list()).toEqual([]);
  });

  it('degrada sin lanzar cuando sessionStorage lanza al leer o escribir', () => {
    vi.stubGlobal('sessionStorage', {
      getItem: () => {
        throw new Error('bloqueado');
      },
      setItem: () => {
        throw new Error('bloqueado');
      },
    });
    const service = new GenerationTrackerService();

    expect(() => service.add('g1')).not.toThrow();
    expect(service.list()).toEqual(['g1']);
  });
});

import { Injectable } from '@angular/core';

const STORAGE_KEY = 'pendingGenerationIds';

/**
 * Rastrea los ids de las generaciones lanzadas desde esta sesion de
 * navegador (tarea 2.1, requisito "Aviso de generaciones fallidas en la
 * interfaz" de specs/exercise-generation/spec.md): `GenerarComponent`
 * registra el id que devuelve `POST /generations` y `EjerciciosComponent`
 * los consulta para avisar cuando alguna termina en error, ya que el
 * listado de pendientes ya no incluye las fallidas. Se apoya en
 * `sessionStorage` para sobrevivir a una recarga de `/ejercicios`; si no
 * esta disponible (o falla) degrada a un conjunto en memoria -- como mucho
 * se pierde el rastreo al recargar, sin romper la pantalla (design.md
 * decision 4).
 */
@Injectable({ providedIn: 'root' })
export class GenerationTrackerService {
  private ids: string[] = [];
  private loaded = false;
  private readonly storage = resolveStorage();

  add(id: string): void {
    this.ensureLoaded();
    if (this.ids.includes(id)) {
      return;
    }
    this.ids = [...this.ids, id];
    this.persist();
  }

  list(): string[] {
    this.ensureLoaded();
    return [...this.ids];
  }

  remove(id: string): void {
    this.ensureLoaded();
    const next = this.ids.filter((tracked) => tracked !== id);
    if (next.length === this.ids.length) {
      return;
    }
    this.ids = next;
    this.persist();
  }

  private ensureLoaded(): void {
    if (this.loaded) {
      return;
    }
    this.loaded = true;
    if (!this.storage) {
      return;
    }
    try {
      const raw = this.storage.getItem(STORAGE_KEY);
      if (!raw) {
        return;
      }
      const parsed: unknown = JSON.parse(raw);
      if (Array.isArray(parsed)) {
        this.ids = parsed.filter((item): item is string => typeof item === 'string');
      }
    } catch {
      this.ids = [];
    }
  }

  private persist(): void {
    if (!this.storage) {
      return;
    }
    try {
      this.storage.setItem(STORAGE_KEY, JSON.stringify(this.ids));
    } catch {
      // sin persistencia: el estado en memoria sigue siendo valido.
    }
  }
}

function resolveStorage(): Storage | null {
  try {
    return typeof sessionStorage === 'undefined' ? null : sessionStorage;
  } catch {
    return null;
  }
}

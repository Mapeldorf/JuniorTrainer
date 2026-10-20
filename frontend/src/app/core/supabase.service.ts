import { Injectable } from '@angular/core';
import { createClient, Session, SupabaseClient } from '@supabase/supabase-js';
import { environment } from '../../environments/environment';

/**
 * Unico punto de acceso a Supabase Auth desde el frontend: login, logout,
 * recuperacion de contrasena y alta de contrasena desde una invitacion.
 * El resto de datos de la aplicacion (generaciones, bloques, asignaciones,
 * respuestas) pasan siempre por el backend, nunca por este cliente.
 */
@Injectable({ providedIn: 'root' })
export class SupabaseService {
  readonly client: SupabaseClient = createClient(
    environment.supabaseUrl,
    environment.supabasePublishableKey,
  );

  async signInWithPassword(email: string, password: string) {
    return this.client.auth.signInWithPassword({ email, password });
  }

  async signOut() {
    return this.client.auth.signOut();
  }

  async requestPasswordReset(email: string, redirectTo: string) {
    return this.client.auth.resetPasswordForEmail(email, { redirectTo });
  }

  async updatePassword(password: string) {
    return this.client.auth.updateUser({ password });
  }

  async getSession(): Promise<Session | null> {
    const { data } = await this.client.auth.getSession();
    return data.session;
  }

  /** Fuerza la renovacion del access token contra Supabase Auth (se usa
   * como reintento cuando el backend rechaza el token por caducado pese a
   * que `getSession()` lo diera por valido, p.ej. por sesgo de reloj). */
  async refreshSession(): Promise<Session | null> {
    const { data } = await this.client.auth.refreshSession();
    return data.session;
  }

  /** Rol leido de los metadatos del JWT (los mismos que crean el Profile al alta). */
  async getRole(): Promise<'tech_lead' | 'student' | null> {
    const session = await this.getSession();
    const role = session?.user.user_metadata?.['role'];
    return role === 'tech_lead' || role === 'student' ? role : null;
  }
}

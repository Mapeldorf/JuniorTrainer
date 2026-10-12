import { Component, inject } from '@angular/core';
import { Router, RouterLink, RouterLinkActive } from '@angular/router';
import { BrandMarkComponent } from '../../core/brand-mark';
import { SupabaseService } from '../../core/supabase.service';

/**
 * Cabecera de navegacion del tech lead (tarea 3.1 de
 * frontend-tech-lead-ejercicios, ampliada en la tarea 6.1 de
 * frontend-tech-lead-bloques y en la tarea 4.2 de
 * frontend-tech-lead-alumnos): las tres pestanas de la seccion 10 --
 * "Ejercicios guardados" (`/ejercicios`), "Bloques de ejercicios"
 * (`/bloques`) y "Alumnos" (`/alumnos`) -- ya estan todas activas.
 * Incluye "Cerrar sesion" (igual que `home`/`mis-bloques`): es el shell
 * compartido de todas las pantallas del tech lead, que ya no aterriza en
 * el `home` placeholder.
 */
@Component({
  selector: 'app-tech-lead-nav',
  standalone: true,
  imports: [RouterLink, RouterLinkActive, BrandMarkComponent],
  templateUrl: './tech-lead-nav.html',
})
export class TechLeadNavComponent {
  private readonly supabase = inject(SupabaseService);
  private readonly router = inject(Router);

  async signOut(): Promise<void> {
    await this.supabase.signOut();
    await this.router.navigate(['/login']);
  }
}

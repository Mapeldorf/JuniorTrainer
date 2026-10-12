import { Component, inject } from '@angular/core';
import { Router, RouterLink, RouterLinkActive } from '@angular/router';
import { BrandMarkComponent } from '../../core/brand-mark';
import { SupabaseService } from '../../core/supabase.service';

/**
 * Cabecera de navegacion del tech lead (tarea 3.1, design.md decision
 * 6): las tres pestanas de la seccion 10 -- solo "Ejercicios guardados"
 * esta activa y enlazada a `/ejercicios` en este change; "Bloques de
 * ejercicios" y "Alumnos" se muestran deshabilitadas ("Proximamente"),
 * sin `routerLink`, para no poder navegar a ellas antes de que existan
 * (llegan en los 2 changes siguientes de paso 5, sin tocar esta cabecera
 * de nuevo). Incluye "Cerrar sesion" (igual que `home`/`mis-bloques`):
 * es el shell compartido de todas las pantallas del tech lead, que ya no
 * aterriza en el `home` placeholder.
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

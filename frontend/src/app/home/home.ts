import { Component, OnInit, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { Session } from '@supabase/supabase-js';
import { BrandMarkComponent } from '../core/brand-mark';
import { SupabaseService } from '../core/supabase.service';

/**
 * Placeholder post-login: confirma que la sesion y el rol se leen bien.
 * Las pantallas reales de cada rol llegan en los pasos 4 y 5 del plan de trabajo.
 */
@Component({
  selector: 'app-home',
  standalone: true,
  imports: [BrandMarkComponent],
  templateUrl: './home.html',
})
export class HomeComponent implements OnInit {
  private readonly supabase = inject(SupabaseService);
  private readonly router = inject(Router);

  readonly session = signal<Session | null>(null);
  readonly role = signal<string | null>(null);

  async ngOnInit(): Promise<void> {
    this.session.set(await this.supabase.getSession());
    this.role.set(await this.supabase.getRole());
  }

  async signOut(): Promise<void> {
    await this.supabase.signOut();
    await this.router.navigate(['/login']);
  }
}

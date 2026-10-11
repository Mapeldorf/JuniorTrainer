import { Component, inject, signal } from '@angular/core';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { BrandMarkComponent } from '../../core/brand-mark';
import { SupabaseService } from '../../core/supabase.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, BrandMarkComponent],
  templateUrl: './login.html',
})
export class LoginComponent {
  private readonly fb = inject(FormBuilder);
  private readonly supabase = inject(SupabaseService);
  private readonly router = inject(Router);

  readonly form = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', Validators.required],
  });

  readonly submitting = signal(false);
  readonly error = signal<string | null>(null);

  async submit(): Promise<void> {
    if (this.form.invalid || this.submitting()) {
      return;
    }
    this.submitting.set(true);
    this.error.set(null);

    const { email, password } = this.form.getRawValue();
    const { error } = await this.supabase.signInWithPassword(email, password);

    this.submitting.set(false);

    if (error) {
      this.error.set('Email o contraseña incorrectos.');
      return;
    }

    // Las pantallas propias de cada rol (tech lead / alumno) llegan en los
    // pasos 4 y 5 del plan de trabajo; de momento ambas caen en el mismo home.
    await this.router.navigate(['/']);
  }
}

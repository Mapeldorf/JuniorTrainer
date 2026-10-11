import { Component, inject, signal } from '@angular/core';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { BrandMarkComponent } from '../../core/brand-mark';
import { SupabaseService } from '../../core/supabase.service';

@Component({
  selector: 'app-forgot',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, BrandMarkComponent],
  templateUrl: './forgot.html',
})
export class ForgotComponent {
  private readonly fb = inject(FormBuilder);
  private readonly supabase = inject(SupabaseService);

  readonly form = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
  });

  readonly submitting = signal(false);
  // La respuesta es igual exista o no el email (seccion 2 de la especificacion).
  readonly sent = signal(false);

  async submit(): Promise<void> {
    if (this.form.invalid || this.submitting()) {
      return;
    }
    this.submitting.set(true);

    const { email } = this.form.getRawValue();
    await this.supabase.requestPasswordReset(email, `${window.location.origin}/set-password`);

    this.submitting.set(false);
    this.sent.set(true);
  }
}

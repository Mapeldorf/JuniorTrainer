import { Component, OnInit, inject, signal } from '@angular/core';
import { ReactiveFormsModule, FormBuilder, Validators, AbstractControl, ValidationErrors } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { BrandMarkComponent } from '../../core/brand-mark';
import { SupabaseService } from '../../core/supabase.service';

function passwordsMatch(control: AbstractControl): ValidationErrors | null {
  const password = control.get('password')?.value;
  const repeat = control.get('repeat')?.value;
  return password && repeat && password !== repeat ? { mismatch: true } : null;
}

/**
 * Pantalla de "elegir contraseña", comun al enlace de invitacion de un
 * alumno y al enlace de recuperacion de contrasena: en ambos casos Supabase
 * abre esta URL con una sesion ya activa (detectSessionInUrl) y solo falta
 * pedir la contrasena nueva.
 */
@Component({
  selector: 'app-set-password',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, BrandMarkComponent],
  templateUrl: './set-password.html',
})
export class SetPasswordComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly supabase = inject(SupabaseService);
  private readonly router = inject(Router);

  readonly form = this.fb.nonNullable.group(
    {
      password: ['', [Validators.required, Validators.minLength(8)]],
      repeat: ['', Validators.required],
    },
    { validators: passwordsMatch },
  );

  readonly submitting = signal(false);
  readonly error = signal<string | null>(null);
  /** null mientras se comprueba la sesion; false si el enlace no era valido */
  readonly linkValid = signal<boolean | null>(null);

  async ngOnInit(): Promise<void> {
    const session = await this.supabase.getSession();
    this.linkValid.set(session !== null);
  }

  async submit(): Promise<void> {
    if (this.form.invalid || this.submitting()) {
      return;
    }
    this.submitting.set(true);
    this.error.set(null);

    const { password } = this.form.getRawValue();
    const { error } = await this.supabase.updatePassword(password);

    this.submitting.set(false);

    if (error) {
      this.error.set('No se ha podido guardar la contraseña. Prueba de nuevo.');
      return;
    }

    await this.router.navigate(['/']);
  }
}

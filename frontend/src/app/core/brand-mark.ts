import { Component } from '@angular/core';

@Component({
  selector: 'app-brand-mark',
  template: `
    <div class="flex items-center gap-3">
      <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#ffffff"
             stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M9 8l-4 4 4 4M15 8l4 4-4 4" />
        </svg>
      </div>
      <span class="text-lg font-semibold text-content">JuniorTrainer</span>
    </div>
  `,
})
export class BrandMarkComponent {}

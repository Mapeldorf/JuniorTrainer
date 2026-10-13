import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { ConfirmDialogComponent } from './core/confirm-dialog';

@Component({
  imports: [RouterOutlet, ConfirmDialogComponent],
  selector: 'app-root',
  templateUrl: './app.html',
})
export class App {}

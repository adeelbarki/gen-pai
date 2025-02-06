import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { AuthService } from './core/services/auth.service';
import { Router } from '@angular/router';
import { NgIf } from '@angular/common';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, NgIf],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  title = 'Angular Cognito Auth';

  constructor(private authService: AuthService, private router: Router) {}

  async logout() {
    // await this.authService.logout();
    this.router.navigate(['/auth/login']); // Redirect to login page after logout
  }

  get isAuthenticated(): boolean {
    return this.authService.isAuthenticated();
  }
}

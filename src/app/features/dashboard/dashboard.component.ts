import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { NgIf } from '@angular/common';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [NgIf],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.css'
})
export class DashboardComponent {
  user: any = null;

  constructor(private authService: AuthService, private router: Router) {}

  async ngOnInit() {
    try {
      this.user = await this.authService.getCurrentUser();
    } catch (error) {
      console.error('User not authenticated:', error);
      this.router.navigate(['/auth/login']); // ✅ Redirect to login if not authenticated
    }
  }

  async logout() {
    await this.authService.logout();
    this.router.navigate(['/auth/login']); // ✅ Redirect to login after logout
  }
}

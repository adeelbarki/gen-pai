import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { AuthService } from './core/services/auth.service';
import { Router } from '@angular/router';
import { NgIf } from '@angular/common';
import { AmplifyAuthenticatorModule } from '@aws-amplify/ui-angular';
import { Amplify } from 'aws-amplify';
import { environment } from '../environments/environment';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, NgIf, AmplifyAuthenticatorModule],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  title = 'Angular Cognito Auth';

  constructor(private authService: AuthService, private router: Router) {
    Amplify.configure(environment.amplifyConfig);
  }

  async signOut() {
    
  }

  async logout() {
    // await this.authService.logout();
    this.router.navigate(['/auth/login']); // Redirect to login page after logout
  }

  get isAuthenticated(): boolean {
    return this.authService.isAuthenticated();
  }
}

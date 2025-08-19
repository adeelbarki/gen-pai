import { Component } from '@angular/core';
import { AuthService } from './core/services/auth.service';
import { Router } from '@angular/router';
import { AmplifyAuthenticatorModule } from '@aws-amplify/ui-angular';
import { Amplify } from 'aws-amplify';
import { environment } from '../environments/environment';
import { AppLayoutComponent } from './features/app-layout/app-layout.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    AmplifyAuthenticatorModule, 
    AppLayoutComponent],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  title = 'Angular Cognito Auth';

  constructor(private authService: AuthService, private router: Router) {
    Amplify.configure(environment.amplifyConfig);
  }


}

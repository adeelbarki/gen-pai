import { Injectable } from '@angular/core';
import { Router } from '@angular/router';

@Injectable({
  providedIn: 'root'
})

export class AuthService {
  constructor(private router: Router) {}

  login(username: string, password: string): boolean {
    const storedUser = JSON.parse(localStorage.getItem('user') || '{}');

    if (storedUser && storedUser.username === username && storedUser.password === password) {
      localStorage.setItem('token', 'dummy-jwt-token');
      return true;
    }
    return false;
  }

  register(username: string, password: string, email: string): boolean {
    const user = { username, password, email };
    localStorage.setItem('user', JSON.stringify(user));
    return true;
  }

  logout() {
    localStorage.removeItem('token');
    this.router.navigate(['/auth/login']);
  }

  isAuthenticated(): boolean {
    return !!localStorage.getItem('token');
  }
}

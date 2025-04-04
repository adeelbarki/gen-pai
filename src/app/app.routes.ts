import { Routes } from '@angular/router';
import { provideRouter } from '@angular/router';

export const routes: Routes = [
    { path: '', redirectTo: 'auth/login', pathMatch: 'full' },
    {
        path: 'auth',
        loadChildren: () => import('./features/auth.routes').then(m => m.AUTH_ROUTES)
      },
    { path: '**', redirectTo: 'auth/login' }
];

export const APP_ROUTER_PROVIDERS = provideRouter(routes);

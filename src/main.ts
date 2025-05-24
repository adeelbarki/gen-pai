import { provideHttpClient } from "@angular/common/http";
import { enableProdMode, importProvidersFrom } from "@angular/core";
import { bootstrapApplication } from '@angular/platform-browser';
import { AppComponent } from './app/app.component';

bootstrapApplication(AppComponent, {
  providers: [provideHttpClient()],
})
  .catch((err) => console.error(err));

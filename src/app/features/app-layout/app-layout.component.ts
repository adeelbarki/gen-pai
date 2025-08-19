import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { StudiesComponent } from './studies/studies.component';
import { DashboardComponent } from './dashboard/dashboard.component';

@Component({
  selector: 'app-layout',
  standalone: true,
  imports: [
    CommonModule,
    StudiesComponent,
    DashboardComponent
  ],
  templateUrl: './app-layout.component.html',
  styleUrl: './app-layout.component.css'
})

export class AppLayoutComponent {
    @Input() signOut!: () => void;
    activeTab: string = 'Dashboard';
    patientId: string = "54862509-2480-4d58-99b8-7e6fe993875b";

    tabs = [
    { name: 'Dashboard', label: 'Dashboard' },
    { name: 'Studies', label: 'Studies' },
    { name: 'History', label: 'History' },
    { name: 'Profile', label: 'Profile' },
    { name: 'Help', label: 'Help' },
  ];

  setActiveTab(tabName: string) {
    this.activeTab = tabName;
  }
}
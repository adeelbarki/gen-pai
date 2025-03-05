import { Component, Input } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { CommonModule } from '@angular/common';
import { ChatSidebarComponent } from './ChatSidebarComponent/chat-sidebar.component';
import { ChatWindowComponent } from './ChatWindowComponent/chat-window.component';
import { MedicalTimelineComponent } from './MedicalTimelineComponent/medical-timeline.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    ChatSidebarComponent,
    ChatWindowComponent,
    MedicalTimelineComponent,
    CommonModule
  ],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.css'
})
export class DashboardComponent {
  @Input() signOut!: () => void;
  activeTab: string = 'Dashboard';

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

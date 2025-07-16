import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ChatSidebarComponent } from './ChatSidebarComponent/chat-sidebar.component';
import { ChatWindowComponent } from './ChatWindowComponent/chat-window.component';
import { MedicalTimelineComponent } from './MedicalTimelineComponent/medical-timeline.component';
import { StudyImageViewerComponent } from './StudyImageViewerComponent/study-image-viewer.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    ChatSidebarComponent,
    ChatWindowComponent,
    MedicalTimelineComponent,
    StudyImageViewerComponent,
    CommonModule
  ],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.css'
})
export class DashboardComponent {
  @Input() signOut!: () => void;
  patientId: string = "54ade882-3ada-4442-b66e-740b5a65e014";
  activeTab: string = 'Dashboard';

  tabs = [
    { name: 'Dashboard', label: 'Dashboard' },
    { name: 'Studies', label: 'Studies' },
    { name: 'History', label: 'History' },
    { name: 'Profile', label: 'Profile' },
    { name: 'Help', label: 'Help' },
  ];

  studies = {
  'X-ray': ['xray1.png', 'xray2.png'],
  'MRI': ['mri1.png'],
  'CT Scan': ['ct1.png', 'ct2.png']
  };

  expanded: string | null = null;
  selectedImage: string | null = null;

  setActiveTab(tabName: string) {
    this.activeTab = tabName;
  }

  toggleExpand(modality: string) {
    this.expanded = this.expanded === modality ? null : modality;
}

  selectImage(image: string) {
    this.selectedImage = image;
}
}

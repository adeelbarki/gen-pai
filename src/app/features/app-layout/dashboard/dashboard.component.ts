import { Component, Input } from '@angular/core';
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
  styleUrl: './dashboard.component.css',
  host: {
    class: 'flex flex-1 w-full h-full gap-4 min-h-0'
  }
})

export class DashboardComponent {
    patientId: string = "54862509-2480-4d58-99b8-7e6fe993875b";
    
    expanded: string | null = null;
    selectedImage: string | null = null;

    toggleExpand(modality: string) {
    this.expanded = this.expanded === modality ? null : modality;
    }

    selectImage(image: string) {
    this.selectedImage = image;
}
}


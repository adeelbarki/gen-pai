import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { EventPillComponent } from './EventPillComponent/event-pill.component';

@Component({
  selector: 'app-medical-timeline',
  standalone: true,
  imports: [CommonModule, EventPillComponent],
  templateUrl: './medical-timeline.component.html'
})

export class MedicalTimelineComponent {
    activeTab: string = 'Events';

  setActiveTab(tabName: string) {
    this.activeTab = tabName;
  }

}
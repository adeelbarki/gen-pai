import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-medical-timeline',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './medical-timeline.component.html'
})

export class MedicalTimelineComponent {
    activeTab: string = 'Events';

  setActiveTab(tabName: string) {
    this.activeTab = tabName;
  }

}
import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { EventPillComponent } from './EventPillComponent/event-pill.component';
import { AccordionListComponent } from './AccordionList/accordion-list.component';

@Component({
  selector: 'app-medical-timeline',
  standalone: true,
  imports: [CommonModule, EventPillComponent, AccordionListComponent],
  templateUrl: './medical-timeline.component.html'
})

export class MedicalTimelineComponent {
    activeTab: string = 'Events';

    historyItems = ['Gathering History', 'Analyzing History'];
    examItems = ['Fetching Physical Exam', 'Analyzing Physical Exam'];
    resultsItems = ['Fetching Medical Reports', 'Analyzing Medical Reports', 'Predictions'];

  setActiveTab(tabName: string) {
    this.activeTab = tabName;
  }

}
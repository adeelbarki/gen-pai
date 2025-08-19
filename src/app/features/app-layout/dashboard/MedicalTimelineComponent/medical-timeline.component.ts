import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { EventPillComponent } from './EventPillComponent/event-pill.component';
import { AccordionListComponent } from './AccordionList/accordion-list.component';
import { EventsStatusService } from '../../../../core/services/events-status.service';
import { Observable } from 'rxjs';

@Component({
  selector: 'app-medical-timeline',
  standalone: true,
  imports: [CommonModule, EventPillComponent, AccordionListComponent],
  templateUrl: './medical-timeline.component.html',
  host: {
    class: 'relative w-full h-full bg-white shadow-md rounded-lg p-4 flex flex-col'
  }
})

export class MedicalTimelineComponent {
    activeTab: string = 'Events';

    historyItems = ['Gathering', 'Analyzing'];
    examItems = ['Fetching', 'Analyzing'];
    resultsItems = ['Fetching Medical Reports', 'Analyzing Reports', 'Predictions'];

    gatheringDone$!: Observable<boolean>;

    constructor(private eventsStatus: EventsStatusService) {
    this.gatheringDone$ = this.eventsStatus.gatheringHistoryDoneObs;
  }

  setActiveTab(tabName: string) {
    this.activeTab = tabName;
  }

}
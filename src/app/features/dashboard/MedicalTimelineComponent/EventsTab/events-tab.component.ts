import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AccordionListComponent } from '../AccordionList/accordion-list.component';

@Component({
  selector: 'app-events-tab',
  standalone: true,
  imports: [CommonModule, AccordionListComponent],
  templateUrl: './events-tab.component.html'
})
export class EventsTabComponent {
  @Input() historyItems: string[] = ['Gathering History', 'Analyzing History'];
  @Input() examItems: string[] = ['Fetching Physical Exam', 'Analyzing Physical Exam'];
  @Input() resultsItems: string[] = ['Fetching Medical Reports', 'Analyzing Medical Reports', 'Predictions'];
}

import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CommonModule } from '@angular/common';


@Component({
  selector: 'app-event-pill',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './event-pill.component.html',
  host: { class: 'w-full flex items-center justify-center' }
})

export class EventPillComponent {
   @Input() active = false
   @Input() label = 'E'

   @Input() tabValue: string = 'Events'
   @Output() tabChange = new EventEmitter<string>();

   onClick() {
    this.tabChange.emit(this.tabValue)
   }
}
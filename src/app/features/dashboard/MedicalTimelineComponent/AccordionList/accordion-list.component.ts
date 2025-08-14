import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-accordion',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './accordion-list.component.html',
  styleUrls: ['./accordion-list.component.css']
})
export class AccordionListComponent {
  @Input() title = '';
  @Input() items: string[] = [];
  @Input() open = false;
  @Input() rightIconFor?: string;
  @Input() rightIconIndex?: number;
  @Input() blinkIconFor?: string;
  @Input() blinkIconIndex?: number;

  showIcon(it: string, i: number): boolean {
    if (this.rightIconIndex !== undefined && this.rightIconIndex !== null) {
      return i === this.rightIconIndex;
    }
    if (this.rightIconFor) {
      // tolerant compare: trim + lowercase
      return it?.trim().toLowerCase() === this.rightIconFor.trim().toLowerCase();
    }
    return false;
  }

  shouldBlink(it: string, i: number): boolean {
    if (this.blinkIconIndex != null) return i === this.blinkIconIndex;
    if (this.blinkIconFor) return it?.trim().toLowerCase() === this.blinkIconFor.trim().toLowerCase();
    return false;
  }

  toggle() { this.open = !this.open; }
}

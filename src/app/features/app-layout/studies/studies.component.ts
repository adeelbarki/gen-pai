import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { StudyImageViewerComponent } from './StudyImageViewerComponent/study-image-viewer.component';

@Component({
  selector: 'app-studies',
  standalone: true,
  imports: [
    CommonModule,
    StudyImageViewerComponent,
  ],
  templateUrl: './studies.component.html',
  host: {
    class: 'flex flex-1 gap-4'
  }
})
export class StudiesComponent {
    patientId: string = "54862509-2480-4d58-99b8-7e6fe993875b";

    studies = {
    'X-ray': ['xray1.png', 'xray2.png'],
    'MRI': ['mri1.png'],
    'CT Scan': ['ct1.png', 'ct2.png']
    };

    expanded: string | null = null;
    selectedImage: string | null = null;

    toggleExpand(modality: string) {
        this.expanded = this.expanded === modality ? null : modality;
    }

    selectImage(image: string) {
        this.selectedImage = image;
    }
}
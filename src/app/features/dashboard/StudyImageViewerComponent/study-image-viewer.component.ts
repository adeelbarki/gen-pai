import { Component, Input, OnChanges } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-study-image-viewer',
  imports: [
      CommonModule
    ],
  templateUrl: './study-image-viewer.component.html',
  styleUrls: ['./study-image-viewer.component.css']
})

export class StudyImageViewerComponent implements OnChanges {
  @Input() imageName: string | null = null;
  presignedUrl: string | null = null;
  loading = false;
  error: string | null = null;

  constructor(private http: HttpClient) {}

  ngOnChanges() {
    if (this.imageName) {
      this.fetchPresignedUrl(this.imageName);
    }
  }

  fetchPresignedUrl(patientId: string) {
    this.loading = true;
    this.presignedUrl = null;
    this.error = null;

    this.http.get<{ url: string }>(`http://localhost:5000/image-url/54ade882-3ada-4442-b66e-740b5a65e014`)
      .subscribe({
        next: (res) => {
          this.presignedUrl = res.url;
          this.loading = false;
          console.log('Fetched URL:', res.url);
        },
        error: (err) => {
          this.error = 'Failed to fetch image';
          this.loading = false;
        }
      });
  }
}
import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class EventsStatusService {
  private gatheringHistoryDone$ = new BehaviorSubject<boolean>(false);
  gatheringHistoryDoneObs = this.gatheringHistoryDone$.asObservable();

  setGatheringHistoryDone(done: boolean) {
    this.gatheringHistoryDone$.next(done);
  }
}

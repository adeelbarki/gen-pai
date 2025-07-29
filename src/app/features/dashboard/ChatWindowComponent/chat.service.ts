import { Injectable } from "@angular/core";
import { HttpClient } from "@angular/common/http";
import { Observable } from "rxjs";
import { ChatResponse } from "./chat.model";

@Injectable({
    providedIn: 'root'
})

export class ChatService {
    private apiUrl = 'http://localhost:5268/api/patient/query';

    // constructor(private http: HttpClient) {}

    sendMessage(text: string, sessionId: string = "default-session"): Observable<string> {
  return new Observable(observer => {
    const body = {
      sessionId: sessionId,
      text: text
    };

    fetch(this.apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(body)
    }).then(response => {
      const reader = response.body?.getReader();
      const decoder = new TextDecoder("utf-8");

      const read = () => {
        reader?.read().then(({ done, value }) => {
          if (done) {
            observer.complete();
            return;
          }
          const chunk = decoder.decode(value, { stream: true });
          observer.next(chunk);
          read();
        });
      };

      read();
    }).catch(err => observer.error(err));
  });
}
}
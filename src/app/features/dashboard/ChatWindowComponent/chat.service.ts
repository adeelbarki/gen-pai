import { Injectable } from "@angular/core";
import { HttpClient } from "@angular/common/http";
import { Observable } from "rxjs";
import { ChatResponse } from "./chat.model";

@Injectable({
    providedIn: 'root'
})

export class ChatService {
    private apiUrl = 'http://localhost:5268/api/patient/query';

    constructor(private http: HttpClient) {}

    sendMessage(text: string, sessionId: string = "default-session"): Observable<ChatResponse> {
       const body = {
            sessionId: sessionId,
            text: text
        };
        return this.http.post<ChatResponse>(this.apiUrl, body);
    }
}
import { Injectable } from "@angular/core";
import { HttpClient } from "@angular/common/http";
import { Observable } from "rxjs";

@Injectable({
    providedIn: 'root'
})

export class ChatService {
    private apiUrl = 'http://localhost:5268/api/patient/query';

    constructor(private http: HttpClient) {}

    sendMessage(text: string): Observable<any> {
        const body = { text }
        return this.http.post<any>(this.apiUrl, body)
    }
}
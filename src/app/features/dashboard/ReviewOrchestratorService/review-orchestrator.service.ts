import { Injectable, Input } from "@angular/core";
import { HttpClient } from "@angular/common/http";
import { Subject, Observable } from "rxjs";

export type Role = 'user' | 'bot' | 'system'
export interface ChatMessage {
    id: string;
    role: Role;
    text: string;
    ts: number
}

@Injectable({ providedIn: 'root'})
export class ReviewOrchestratorService {
    patientId = "54862509-2480-4d58-99b8-7e6fe993875b";
    
    private readonly THANKYOU_TRIGGER = /thanks!\s*i[’']?ve collected everything i need\.?/i;

    private chatOut$ = new Subject<ChatMessage>();

    
    chatMessages$: Observable<ChatMessage> = this.chatOut$.asObservable();
    
    constructor(private http: HttpClient) {}

    onBotMessageDisplayed(text: string) {
        if(!text) return;
        if(this.THANKYOU_TRIGGER.test(text)) {
            this.runAnalysis();
        }
    }

    private runAnalysis() {
        this.pushChat('1) analyzing history and patient exam results...', 'system');

        this.http.get(`http://localhost:5000/analyzing/qa-pexam/${this.patientId}`).subscribe({
            next: () => {
                this.pushChat('2) sent it to doctor for review', 'system');
            },
            error: () => {
                this.pushChat('There was an error during analysis. Please try again.', 'system');
            }
        })
    }

    private pushChat(text: string, role: Role = 'system') {
        this.chatOut$.next({
            id: crypto.randomUUID(),
            role,
            text,
            ts: Date.now()
        })
    }
}


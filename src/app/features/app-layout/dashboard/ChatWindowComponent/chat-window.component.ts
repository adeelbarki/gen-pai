  import { Component, ElementRef, ViewChild, OnInit } from '@angular/core';
  import { ChatService } from './chat.service';
  import { FormsModule } from '@angular/forms';
  import { CommonModule } from '@angular/common';
  import { MarkdownModule } from 'ngx-markdown';
  import { EventsStatusService } from '../../../../core/services/events-status.service';
  import { ReviewOrchestratorService } from '../../ReviewOrchestratorService/review-orchestrator.service';


  @Component({
    selector: 'app-chat-window',
    standalone: true,
    templateUrl: './chat-window.component.html',
    imports: [
        CommonModule,
        FormsModule,
        MarkdownModule
      ],
      styleUrl: './chat-window.component.css',
    host: {
    class: 'w-full h-full bg-white shadow-lg rounded-lg p-6 flex flex-col'
  }
  })

  export class ChatWindowComponent {

    patientId = "54862509-2480-4d58-99b8-7e6fe993875b"
    message: string = ''
    loading: boolean = false;
    loadingInterval: any;

    chatLog: { role: 'user' | 'ai', text: string }[] = [];

    @ViewChild('scrollContainer') private scrollContainer!: ElementRef;

    constructor(
      private chatService: ChatService, 
      private eventsStatus: EventsStatusService,
      private orchestrator: ReviewOrchestratorService) {}

    ngOnInit() {
    this.orchestrator.chatMessages$.subscribe((msg) => {
      this.chatLog.push({ role: 'ai', text: msg.text });
      this.scrollToBottom();
      });
    }


    private containsCompletionPhrase(s: string): boolean {
    const norm = (x: string) => x.replace(/[’]/g, "'").toLowerCase();
    const needle = "thanks! i've collected everything i need.";
    return norm(s).includes(needle);
  }

    sendMessage() {
      const userText = this.message;
      this.chatLog.push({ role: 'user', text: this.message });
      this.chatLog.push({ role: 'ai', text: '' });

      let aiIndex = this.chatLog.length - 1;

      this.chatService.sendMessage(this.message, this.patientId).subscribe({
      next: (chunk: string) => {
        this.chatLog[aiIndex].text += chunk;
        const fullBotText = this.chatLog[aiIndex].text;
        if (this.containsCompletionPhrase(this.chatLog[aiIndex].text)) {
          this.eventsStatus.setGatheringHistoryDone(true);
          this.orchestrator.onBotMessageDisplayed(fullBotText);
        }
        this.scrollToBottom();
      },
      error: (err) => {
        console.error("Streaming error:", err);
        this.chatLog[aiIndex].text += "\n[Error receiving reply]";
      },
      complete: () => {
        this.message = '';
      }
      });
    }
    
    autoResize(event: Event) {
    const textarea = event.target as HTMLTextAreaElement;
    textarea.style.height = 'auto';
    textarea.style.height = `${textarea.scrollHeight}px`;
  }

  private scrollToBottom() {
      try {
        this.scrollContainer.nativeElement.scrollTop = this.scrollContainer.nativeElement.scrollHeight;
      } catch (err) {
        console.error('Scroll error:', err);
      }
    }
  }

  import { Component, ElementRef, ViewChild } from '@angular/core';
  import { ChatService } from './chat.service';
  import { FormsModule } from '@angular/forms';
  import { CommonModule } from '@angular/common';
  import { MarkdownModule } from 'ngx-markdown';
  import { EventsStatusService } from '../../../core/services/events-status.service';


  @Component({
    selector: 'app-chat-window',
    standalone: true,
    templateUrl: './chat-window.component.html',
    imports: [
        CommonModule,
        FormsModule,
        MarkdownModule
      ],
      styleUrl: './chat-window.component.css'
  })

  export class ChatWindowComponent {

    patientId = "54862509-2480-4d58-99b8-7e6fe993875b"
    message: string = ''
    loading: boolean = false;
    loadingInterval: any;

    
    constructor(private chatService: ChatService, private eventsStatus: EventsStatusService) {}

    chatLog: { role: 'user' | 'ai', text: string }[] = [];

    @ViewChild('scrollContainer') private scrollContainer!: ElementRef;


    private containsCompletionPhrase(s: string): boolean {
    // handle straight/curly apostrophes
    const norm = (x: string) => x.replace(/[’]/g, "'").toLowerCase();
    const needle = "thanks! i've collected everything i need.";
    return norm(s).includes(needle);
  }

    sendMessage() {
      this.chatLog.push({ role: 'user', text: this.message });
      this.chatLog.push({ role: 'ai', text: '' });

      let aiIndex = this.chatLog.length - 1;

      this.chatService.sendMessage(this.message, this.patientId).subscribe({
      next: (chunk: string) => {
        this.chatLog[aiIndex].text += chunk;
        if (this.containsCompletionPhrase(this.chatLog[aiIndex].text)) {
          this.eventsStatus.setGatheringHistoryDone(true);
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


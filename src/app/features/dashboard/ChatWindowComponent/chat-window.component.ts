import { Component, ElementRef, ViewChild } from '@angular/core';
import { ChatService } from './chat.service';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { ChatResponse } from './chat.model';

@Component({
  selector: 'app-chat-window',
  standalone: true,
  templateUrl: './chat-window.component.html',
  imports: [
      CommonModule,
      FormsModule,
    ],
})

export class ChatWindowComponent {

  message: string = ''
  loading: boolean = false;
  loadingInterval: any;

  
  constructor(private chatService: ChatService) {}

  chatLog: { role: 'user' | 'ai', text: string }[] = [];

  @ViewChild('scrollContainer') private scrollContainer!: ElementRef;


  sendMessage() {
    this.chatLog.push({ role: 'user', text: this.message });
this.chatLog.push({ role: 'ai', text: '' });

let aiIndex = this.chatLog.length - 1;

this.chatService.sendMessage(this.message, "abc123").subscribe({
  next: (chunk: string) => {
    this.chatLog[aiIndex].text += chunk;
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


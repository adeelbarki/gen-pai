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
    if(!this.message.trim()) return;

    this.chatLog.push({ role: 'user', text: this.message });

      this.loading = true;
      let loadingIndex = this.chatLog.length;
      this.chatLog.push({ role: 'ai', text: '...' });

      let dotCount = 1;
      this.loadingInterval = setInterval(() => {
      let dots = '.'.repeat(dotCount);
      // this.chatLog[loadingIndex].text = `AI is thinking${dots}`;
      dotCount = (dotCount % 3) + 1;
        }, 100);

    this.chatService.sendMessage(this.message).subscribe( {

    next: (response: ChatResponse) => {
    clearInterval(this.loadingInterval);
    this.loading = false;

    this.chatLog.pop();

    this.chatLog.push({ role: 'ai', text: response.answer });

    if (response.results && response.results.length > 0) {
      response.results.forEach((item: any, index: number) => {
        const itemText = `#${index + 1}: ${item.name} (${item.score.toFixed(4)}) — ${item.description}`;
        this.chatLog.push({ role: 'ai', text: itemText });
      });
    }

    this.message = '';

    const textarea = document.querySelector('textarea');
    if (textarea) {
      textarea.style.height = 'auto';
    }
    setTimeout(() => this.scrollToBottom(), 0);
  },
  error: (error) => {
    console.error('Error sending message:', error);
    clearInterval(this.loadingInterval);
    this.loading = false;
  },
  complete: () => {
    // Optional: you can log or handle something on completion
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


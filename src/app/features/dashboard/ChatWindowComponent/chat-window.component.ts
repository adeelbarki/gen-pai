import { Component } from '@angular/core';
import { ChatService } from './chat.service';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

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
  
  constructor(private chatService: ChatService) {}

  chatLog: { role: 'user' | 'ai', text: string }[] = [];

  sendMessage() {
    if(!this.message.trim()) return;

    this.chatService.sendMessage(this.message).subscribe(response => {
      this.chatLog.push({ role: 'user', text: this.message });
      this.chatLog.push({ role: 'ai', text: response.answer });
      this.message = '';

      // Reset textarea height after sending
    const textarea = document.querySelector('textarea');
    if (textarea) {
      textarea.style.height = 'auto';
    }
    }, error => {
      console.error('Error sending message:', error)
    })
  }

  autoResize(event: Event) {
  const textarea = event.target as HTMLTextAreaElement;
  textarea.style.height = 'auto';
  textarea.style.height = `${textarea.scrollHeight}px`;
}
}
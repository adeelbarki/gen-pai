import { Component } from '@angular/core';
// import { NgIf } from '@angular/common';

@Component({
  selector: 'app-chat-sidebar',
  // imports: [NgIf],
  standalone: true,
  templateUrl: './chat-sidebar.component.html'
})

export class ChatSidebarComponent {
  activeTab: string = 'history';

  onSearch() {
    
  }

  startNewChat() {
    console.log('Starting a new chat...');
  }
 
}
import { Component } from '@angular/core';

@Component({
  selector: 'app-chat-sidebar',
  standalone: true,
  templateUrl: './chat-sidebar.component.html',
  host: {
    class: 'w-full h-full bg-white shadow-md rounded-lg p-4 flex flex-col'
  }
})

export class ChatSidebarComponent {
  activeTab: string = 'history';

  onSearch() {
    
  }

  startNewChat() {
    console.log('Starting a new chat...');
  }
 
}
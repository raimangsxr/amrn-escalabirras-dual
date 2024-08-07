import { Component, EventEmitter, Output } from '@angular/core';
import { Participant } from '../participant/participant';
import { AppService } from '../services/app.service';

@Component({
  selector: 'app-team-manager-red',
  templateUrl: './team-manager-red.component.html',
  styleUrls: ['./team-manager-red.component.css']
})
export class TeamManagerRedComponent {

  @Output() newParticipantEvent = new EventEmitter<Participant>();
  name: string = '';

  constructor(private appService: AppService) {}

  createParticipant(): void {
    if (this.name != '') {
      const newParticipant = this.appService.createParticipant(this.name);
      this.newParticipantEvent.emit(newParticipant);
    }
  }

  getCurrentParticipant(): Participant | null {
    return this.appService.getCurrentParticipants()[0];
  }
  
}

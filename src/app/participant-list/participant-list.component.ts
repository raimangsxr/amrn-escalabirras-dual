import { Component } from '@angular/core';
import { AppService } from '../services/app.service';
import { Participant } from '../participant/participant';

@Component({
  selector: 'app-participant-list',
  templateUrl: './participant-list.component.html',
  styleUrls: ['./participant-list.component.css']
})
export class ParticipantListComponent {
  constructor(private appService: AppService) { }

  getParticipants(): Participant[] {
    return this.appService.getParticipants().sort((a, b) => (a.id < b.id) ? -1 : ((a.id > b.id) ? 1 : 0)).slice(-10).reverse();
  }

  getParticipantsCount(): number {
    return this.appService.getParticipants().filter(p => p.id > 0).length;
  }

}

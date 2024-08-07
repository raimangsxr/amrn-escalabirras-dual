import { Component, EventEmitter, Output } from "@angular/core";
import { Participant } from '../participant/participant';
import { AppService } from '../services/app.service';

@Component({
  selector: "app-team-manager-blue",
  templateUrl: "./team-manager-blue.component.html",
  styleUrls: ["./team-manager-blue.component.css"]
})
export class TeamManagerBlueComponent {

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
    return this.appService.getCurrentParticipants()[1];
  }
  
}

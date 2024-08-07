import { Component, ElementRef, Input, ViewChild } from "@angular/core";
import { AppService } from '../services/app.service';
import { Participant } from '../participant/participant';

@Component({
  selector: 'app-manager',
  templateUrl: './manager.component.html',
  styleUrls: ['./manager.component.css']
})
export class ManagerComponent {

  @ViewChild('fin', {static: true}) finField!: ElementRef;

  constructor(
    private appService: AppService
  ) { }

  getNewRecord(): Participant | null {
    return this.appService.getNewRecord();
  }

  createParticipant(): void {
  }

  addCrate(team: number): void {
    this.appService.addCrate(team);
  }

  removeCrate(team: number): void {
    this.appService.removeCrate(team);
  }

  finishGame(participant: Participant, team: number): void {
    this.appService.finishGame(participant, team);
  }

  addParticipantRed(participant: Participant): void {
    this.appService.addParticipantToGame(participant, 0);
  }

  addParticipantBlue(participant: Participant): void {
    this.appService.addParticipantToGame(participant, 1);
  }

  getParticipantRed(): Participant {
    return this.appService.getCurrentParticipants()[0];
  }

  getParticipantBlue(): Participant {
    return this.appService.getCurrentParticipants()[1];
  }

}

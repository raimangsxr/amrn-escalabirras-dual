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

  finishGame(): void {
    this.appService.finishGame();
  }

  addParticipantRed(participant: Participant): void {
    this.appService.addParticipantToGame(participant, 0);
  }

  addParticipantBlue(participant: Participant): void {
    this.appService.addParticipantToGame(participant, 1);
  }

}

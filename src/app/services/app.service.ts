import { Injectable } from "@angular/core";
import { Participant } from '../participant/participant';
import JSConfetti from 'js-confetti';

@Injectable({
  providedIn: 'root'
})
export class AppService {

  currentParticipants: Array<Participant> = [{id:0, name:"- - -", crates: 0}, {id:0, name:"- - -", crates: 0}];
  allParticipants: Array<Participant> = [];
  winnerParticipants: Array<Participant> = [];
  jsConfetti = new JSConfetti();
  newRecord: Participant | null = null;
  confettiTime = 10000;
  confettiInterval = 2000;

  constructor() {
    const allParticipants: Participant[] = JSON.parse(localStorage.getItem('allParticipants')!);
    if (!allParticipants) {
      const fillParticipant = this.createParticipant('- - -');
      for (let i = 0; i < 10; i++) {
        this.allParticipants.push(Object.assign({}, fillParticipant));
      }
    } else {
      this.allParticipants = allParticipants;
    }

    const winnerParticipants: Participant[] = JSON.parse(localStorage.getItem('winnerParticipants')!);
    if (!winnerParticipants) {
      const fillParticipant = this.createParticipant('- - -');
      for (let i = 0; i < 10; i++) {
        this.winnerParticipants.push(Object.assign({}, fillParticipant));
      }
    } else {
      this.winnerParticipants = winnerParticipants;
    }
  }

  getCurrentParticipants(): Participant[] {
    return this.currentParticipants;
  }

  private getNextId(): number {
    if (this.allParticipants.length === 0) {
      return 0;
    }
    return Math.max(...this.allParticipants.map(p => p.id)) + 1;
  }

  createParticipant(participantName: string): Participant {
    const newParticipant = {
      id: this.getNextId(),
      name: participantName,
      crates: 0
    } as Participant;
    return newParticipant;
  }

  saveParticipant(participant: Participant): void {
    if (this.allParticipants.length > 0 && this.allParticipants[this.allParticipants.length - 1].crates === 0) {
      this.allParticipants.pop();
    }
    participant.id = this.getNextId();
    this.allParticipants.push(Object.assign({}, participant));
    localStorage.setItem('allParticipants', JSON.stringify(this.allParticipants));
  }

  saveWinnerParticipant(participant: Participant): void {
    if (this.winnerParticipants.length > 0 && this.winnerParticipants[this.winnerParticipants.length - 1].crates === 0) {
      this.winnerParticipants.pop();
    }
    participant.id = this.getNextId();
    this.winnerParticipants.push(Object.assign({}, participant));
    localStorage.setItem('winnerParticipants', JSON.stringify(this.winnerParticipants));
    const bestParticipantCrates = Math.max(...this.winnerParticipants.map(p => p.crates));
    const bestParticipant = this.winnerParticipants.find(p => p.crates === bestParticipantCrates);
    if (!bestParticipant || participant.id == bestParticipant.id)
      this.setNewRecord(participant);
  }

  finishGame(participant: Participant, team: number): void {
    if (participant.id === 0) return;

    this.saveParticipant(participant);
    this.saveWinnerParticipant(participant);
    this.getCurrentParticipants()[team] = {id:0, name:"- - -", crates: 0};
  }

  addCrate(team: number): void {
    if (this.currentParticipants[team].id === 0) {
      return;
    }
    this.currentParticipants[team].crates += 1;
  }

  removeCrate(team: number): void {
    if (this.currentParticipants[team].id === 0) {
      return;
    }
    if (this.currentParticipants[team].crates > 0) {
      this.currentParticipants[team].crates -= 1;
    }
  }

  addParticipantToGame(participant: Participant, team: number): void { // 0 red, 1 blue
    this.currentParticipants[team] = participant;
  }

  getParticipants(): Participant[] {
    return this.allParticipants;
  }

  getWinnerParticipants(): Participant[] {
    return this.winnerParticipants;
  }

  getNewRecord(): Participant | null {
    return this.newRecord;
  }

  setNewRecord(participant: Participant) {
    this.newRecord = participant;
    this.launchConfetti();
    setTimeout(() => {
      this.newRecord = null;
    }, this.confettiTime + this.confettiInterval);
  }

  launchConfetti() {
    let count = this.confettiTime / this.confettiInterval;
    this.jsConfetti.addConfetti({
      confettiRadius: 6,
      confettiNumber: 2000,
    });
    this.jsConfetti.addConfetti({
      emojis: this.pickRandomEmojis()
    });
    const intervalId = setInterval(() => {
      this.jsConfetti.addConfetti({
        confettiRadius: 6,
        confettiNumber: 2000,
      });
      this.jsConfetti.addConfetti({
        emojis: this.pickRandomEmojis()
      });
      count -= 1;
      if (count === 0) {
        clearInterval(intervalId);
      }
    }, this.confettiInterval);
  }

  private pickRandomEmojis(): any {
    const emojis = ['🐵', '🦧', '🧟‍♂️', '🏋️', '🐍', '😎', '🤠', '😱', '😹', '👩‍🦲', '🐞', '😁', '🏍️', '🥇', '🐮', '🙈', '💩', '👻', '🦄'];
    const shuffled = Array.from(emojis).sort(() => 0.5 - Math.random());
    return shuffled.slice(0, 6);
  };

}

import { Component } from '@angular/core';
import { Participant } from '../participant/participant';
import { AppService } from '../services/app.service';

@Component({
  selector: 'app-top3',
  templateUrl: './top3.component.html',
  styleUrls: ['./top3.component.css']
})
export class Top3Component {
  constructor(private appService: AppService) { }

  getTop3(): Participant[] {
    const sortedParticipants = this.appService.getWinnerParticipants().sort(
      (a, b) => (a.crates < b.crates) ? 1 : ((a.crates > b.crates) ? -1 : 0)
    );
    return sortedParticipants.slice(0, 3);
  }
}

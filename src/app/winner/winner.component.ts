import { Component } from '@angular/core';
import { AppService } from '../services/app.service';
import { Participant } from '../participant/participant';

@Component({
  selector: 'app-winner',
  templateUrl: './winner.component.html',
  styleUrls: ['./winner.component.css']
})
export class WinnerComponent {

  constructor(private appService: AppService) {}

  getNewRecord(): Participant | null {
    return this.appService.getNewRecord();
  }

  getBackgroundColor(): boolean {
    return Math.random() > 0.5 ? true : false;
  }
}
